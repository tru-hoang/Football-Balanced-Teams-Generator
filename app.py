from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
import io
import re
import random
import os
from datetime import datetime

app = Flask(__name__)

def get_file_version(filename):
    """Get file version based on modification time for cache busting"""
    static_path = os.path.join(app.root_path, 'static', filename)
    try:
        mtime = os.path.getmtime(static_path)
        return str(int(mtime))
    except OSError:
        # If file doesn't exist, return current timestamp
        return str(int(datetime.now().timestamp()))

def convert_to_export_url(url):
    """Convert Google Sheets URL to export format"""
    # Extract the spreadsheet ID from various URL formats
    # Pattern: /d/{SPREADSHEET_ID}/
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if match:
        spreadsheet_id = match.group(1)
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=xlsx"
    return url  # Return as-is if we can't extract ID

@app.route('/')
def index():
    # Get versions for cache busting
    css_version = get_file_version('style.css')
    js_version = get_file_version('app.js')

    return render_template('index.html',
                         css_version=css_version,
                         js_version=js_version)

def is_goalkeeper(player):
    """Check if a player is a goalkeeper"""
    value = player.get('goalkeeper')
    if value is not None:
        return str(value).upper().strip() == 'YES' or value is True
    return False

def is_main_goalkeeper(player):
    """Check if a player is a main goalkeeper"""
    value = player.get('main_goalkeeper')
    if value is not None:
        return str(value).upper().strip() == 'YES' or value is True
    return False

def get_player_positions(player):
    """Get positions for a player based on position columns marked as 'Yes'"""
    position_columns = {
        'goalkeeper': 'GK',
        'central_defender': 'CD',
        'wing_defender': 'WD',
        'central_midfielder': 'CM',
        'wing_midfielder': 'WM',
        'attacker': 'ATT'
    }
    
    positions = []
    for col, abbrev in position_columns.items():
        value = player.get(col)
        if value is not None:
            if str(value).upper().strip() == 'YES' or value is True:
                positions.append(abbrev)
    
    return ', '.join(positions) if positions else 'N/A'

def count_position_in_team(team, position_col):
    """Count how many players in a team have a specific position"""
    count = 0
    for player in team:
        value = player.get(position_col)
        if value is not None:
            if str(value).upper().strip() == 'YES' or value is True:
                count += 1
    return count

@app.route('/generate_teams')
def generate_teams():
    sheet_url = request.args.get('url')
    if not sheet_url:
        return jsonify({"error": "Sheet URL is required"}), 400
    
    try:
        # Convert to export URL if needed
        export_url = convert_to_export_url(sheet_url)
        response = requests.get(export_url)
        response.raise_for_status()
        
        # Get attending players based on will_attend_next_match column only
        players_df = pd.read_excel(io.BytesIO(response.content), sheet_name='Players')

        # Handle different data types in will_attend_next_match column
        attending_players = []
        for _, player in players_df.iterrows():
            will_attend = player.get('will_attend_next_match')
            if will_attend is not None:
                # Convert to string and check if it's 'YES' (case insensitive) or True
                if str(will_attend).upper() == 'YES' or will_attend is True:
                    attending_players.append(player.to_dict())

        if len(attending_players) < 2:
            return jsonify({"error": "not enough players"}), 400
        
        # Sort by overall rating descending, then shuffle players with same rating for randomness
        attending_players.sort(key=lambda x: x.get('overall_rating', 0), reverse=True)

        # Shuffle players with the same rating to add randomness
        shuffled_players = []
        current_rating = None
        same_rating_group = []

        for player in attending_players:
            rating = player.get('overall_rating', 0)
            if current_rating is None or rating == current_rating:
                same_rating_group.append(player)
                current_rating = rating
            else:
                # Shuffle the group with same rating and add to shuffled list
                random.shuffle(same_rating_group)
                shuffled_players.extend(same_rating_group)
                same_rating_group = [player]
                current_rating = rating

        # Don't forget the last group
        if same_rating_group:
            random.shuffle(same_rating_group)
            shuffled_players.extend(same_rating_group)

        # Step 1: Split Players by Position Pool (Create buckets without duplicating players)
        # Players can appear in multiple buckets based on their positions
        position_buckets = {
            'main_gk': [],
            'gk': [],
            'central_defender': [],
            'wing_defender': [],
            'central_midfielder': [],
            'wing_midfielder': [],
            'attacker': []
        }

        for player in shuffled_players:
            # Check main_goalkeeper first
            if is_main_goalkeeper(player):
                position_buckets['main_gk'].append(player)
            # Check regular goalkeeper
            if is_goalkeeper(player):
                position_buckets['gk'].append(player)
            # Check other positions
            if player.get('central_defender') and str(player.get('central_defender')).upper().strip() == 'YES':
                position_buckets['central_defender'].append(player)
            if player.get('wing_defender') and str(player.get('wing_defender')).upper().strip() == 'YES':
                position_buckets['wing_defender'].append(player)
            if player.get('central_midfielder') and str(player.get('central_midfielder')).upper().strip() == 'YES':
                position_buckets['central_midfielder'].append(player)
            if player.get('wing_midfielder') and str(player.get('wing_midfielder')).upper().strip() == 'YES':
                position_buckets['wing_midfielder'].append(player)
            if player.get('attacker') and str(player.get('attacker')).upper().strip() == 'YES':
                position_buckets['attacker'].append(player)

        # Initialize teams
        team_a = []
        team_b = []
        team_a_rating = 0
        team_b_rating = 0

        # Track assigned players to avoid double assignment
        assigned_players = set()

        # Step 2: Assign Goalkeepers First (Critical Position)
        # Sort GK candidates by rating (descending). Prioritize main_goalkeeper then normal goalkeeper
        gk_candidates = []
        gk_candidates.extend(position_buckets['main_gk'])  # Main GKs first
        # Sort by rating descending
        gk_candidates.sort(key=lambda x: x.get('overall_rating', 0), reverse=True)
        
        gk_candidates.extend([gk for gk in position_buckets['gk'] if gk not in position_buckets['main_gk']])  # Regular GKs

        # Pick top 2 GKs and assign to teams
        available_gks = [gk for gk in gk_candidates[:2] if id(gk) not in assigned_players]

        if len(available_gks) >= 2:
            # Assign strongest GK to weaker team (initially random)
            team_a_gk = available_gks[0]
            team_b_gk = available_gks[1]

            team_a.append(team_a_gk)
            team_a_rating += team_a_gk.get('overall_rating', 0)
            assigned_players.add(id(team_a_gk))

            team_b.append(team_b_gk)
            team_b_rating += team_b_gk.get('overall_rating', 0)
            assigned_players.add(id(team_b_gk))

        # Step 3: Fill Other Positions One by One
        position_assignment_order = ['central_defender', 'wing_defender', 'central_midfielder', 'wing_midfielder', 'attacker']
        random.shuffle(position_assignment_order)  # Shuffle for random priority

        for position in position_assignment_order:
            # Get available candidates (exclude already assigned players)
            candidates = [p for p in position_buckets[position] if id(p) not in assigned_players]

            if not candidates:
                continue

            # Sort by rating (descending)
            candidates.sort(key=lambda x: x.get('overall_rating', 0), reverse=True)

            # Calculate how many players we need for this position (rough estimate)
            total_players_needed = len(shuffled_players) // 2  # Half for each team
            position_players_needed = max(1, len(candidates) // 2)  # At least 1 per team if available

            # Alternating Assignment (Snake Draft)
            for i in range(min(position_players_needed * 2, len(candidates))):
                player = candidates[i]
                if id(player) in assigned_players:
                    continue

                rating = player.get('overall_rating', 0)

                # Assign best available player to the currently weaker team
                if team_a_rating <= team_b_rating:
                    team_a.append(player)
                    team_a_rating += rating
                else:
                    team_b.append(player)
                    team_b_rating += rating

                assigned_players.add(id(player))

        # Step 4: Handle Multi-Position Players and Remaining Players
        # Assign any remaining players (multi-position or unassigned)
        remaining_candidates = [p for p in shuffled_players if id(p) not in assigned_players]

        for player in remaining_candidates:
            rating = player.get('overall_rating', 0)

            # Assign to weaker team
            if team_a_rating <= team_b_rating:
                team_a.append(player)
                team_a_rating += rating
            else:
                team_b.append(player)
                team_b_rating += rating

        # Step 5: Balance Adjustment (Optional but Recommended)
        # Try 1-for-1 swaps within same position to reduce rating difference
        # This is a simplified version - check for potential swaps that improve balance
        rating_difference = abs(team_a_rating - team_b_rating)

        # For each position, try to find swap opportunities
        for position in position_assignment_order:
            # Get players from each team who can play this position
            team_a_position_players = []
            team_b_position_players = []

            for player in team_a:
                if position == 'central_defender' and player.get('central_defender') == 'Yes':
                    team_a_position_players.append(player)
                elif position == 'wing_defender' and player.get('wing_defender') == 'Yes':
                    team_a_position_players.append(player)
                elif position == 'central_midfielder' and player.get('central_midfielder') == 'Yes':
                    team_a_position_players.append(player)
                elif position == 'wing_midfielder' and player.get('wing_midfielder') == 'Yes':
                    team_a_position_players.append(player)
                elif position == 'attacker' and player.get('attacker') == 'Yes':
                    team_a_position_players.append(player)

            for player in team_b:
                if position == 'central_defender' and player.get('central_defender') == 'Yes':
                    team_b_position_players.append(player)
                elif position == 'wing_defender' and player.get('wing_defender') == 'Yes':
                    team_b_position_players.append(player)
                elif position == 'central_midfielder' and player.get('central_midfielder') == 'Yes':
                    team_b_position_players.append(player)
                elif position == 'wing_midfielder' and player.get('wing_midfielder') == 'Yes':
                    team_b_position_players.append(player)
                elif position == 'attacker' and player.get('attacker') == 'Yes':
                    team_b_position_players.append(player)

            # Try swaps between players of same position
            for a_player in team_a_position_players:
                # Skip main goalkeepers from swapping
                if is_main_goalkeeper(a_player):
                    continue
                for b_player in team_b_position_players:
                    # Skip main goalkeepers from swapping
                    if is_main_goalkeeper(b_player):
                        continue

                    a_rating = a_player.get('overall_rating', 0)
                    b_rating = b_player.get('overall_rating', 0)

                    # Calculate new rating difference after swap
                    new_team_a_rating = team_a_rating - a_rating + b_rating
                    new_team_b_rating = team_b_rating - b_rating + a_rating
                    new_difference = abs(new_team_a_rating - new_team_b_rating)

                    # If swap improves balance, perform it
                    if new_difference < rating_difference:
                        # Perform the swap
                        team_a.remove(a_player)
                        team_b.remove(b_player)
                        team_a.append(b_player)
                        team_b.append(a_player)

                        # Update ratings
                        team_a_rating = new_team_a_rating
                        team_b_rating = new_team_b_rating
                        rating_difference = new_difference

                        # Only do one swap per position for simplicity
                        break
                else:
                    continue
                break

        # Final size balancing check
        # If team sizes differ by more than 2 players, balance them
        size_diff = abs(len(team_a) - len(team_b))
        if size_diff > 2:
            # Determine which team is larger and which is smaller
            if len(team_a) > len(team_b):
                larger_team = team_a
                smaller_team = team_b
                larger_team_rating = team_a_rating
                smaller_team_rating = team_b_rating
            else:
                larger_team = team_b
                smaller_team = team_a
                larger_team_rating = team_b_rating
                smaller_team_rating = team_a_rating

            # Find the weakest (lowest rated) non-main goalkeeper player in the larger team
            non_main_gk_candidates = []
            for player in larger_team:
                if not is_main_goalkeeper(player):  # Exclude main goalkeepers
                    non_main_gk_candidates.append(player)

            if non_main_gk_candidates:
                # Sort by rating (ascending - weakest first)
                non_main_gk_candidates.sort(key=lambda x: x.get('overall_rating', 0))

                # Move the weakest player to the smaller team
                player_to_move = non_main_gk_candidates[0]
                player_rating = player_to_move.get('overall_rating', 0)

                # Remove from larger team and add to smaller team
                larger_team.remove(player_to_move)
                smaller_team.append(player_to_move)

                # Update ratings
                if larger_team == team_a:
                    team_a_rating -= player_rating
                    team_b_rating += player_rating
                else:
                    team_b_rating -= player_rating
                    team_a_rating += player_rating

        # No benched players - all players are assigned to teams

        return jsonify({
            "team_a": [{"name": p['name'], "position": get_player_positions(p), "rating": p['overall_rating']} for p in team_a],
            "team_b": [{"name": p['name'], "position": get_player_positions(p), "rating": p['overall_rating']} for p in team_b]
        })
    except Exception as e:
        return jsonify({"error": f"Failed to generate teams: {str(e)}"}), 500

@app.route('/attending_players')
def get_attending_players():
    sheet_url = request.args.get('url')
    if not sheet_url:
        return jsonify({"error": "Sheet URL is required"}), 400
    
    try:
        # Convert to export URL if needed
        export_url = convert_to_export_url(sheet_url)
        response = requests.get(export_url)
        response.raise_for_status()
        
        # Get attending players based on will_attend_next_match column only
        players_df = pd.read_excel(io.BytesIO(response.content), sheet_name='Players')

        # Handle different data types in will_attend_next_match column
        attending_players = []
        for _, player in players_df.iterrows():
            will_attend = player.get('will_attend_next_match')
            if will_attend is not None:
                # Convert to string and check if it's 'YES' (case insensitive) or True
                if str(will_attend).upper() == 'YES' or will_attend is True:
                    attending_players.append(player.to_dict())

        return jsonify([{"name": p['name'], "position": get_player_positions(p), "rating": p['overall_rating']} for p in attending_players])
    except Exception as e:
        return jsonify({"error": f"Failed to load attending players: {str(e)}"}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)