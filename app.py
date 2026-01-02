from flask import Flask, render_template, request, jsonify
import pandas as pd
import requests
import io
import re
import random

app = Flask(__name__)

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
    return render_template('index.html')

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
        
        # Separate goalkeepers from other players
        goalkeepers = [p for p in shuffled_players if is_goalkeeper(p)]
        other_players = [p for p in shuffled_players if not is_goalkeeper(p)]
        
        # Initialize teams
        team_a = []
        team_b = []
        team_a_rating = 0
        team_b_rating = 0
        
        # Step 1: Distribute goalkeepers evenly if there are 2 or more
        if len(goalkeepers) >= 2:
            # Separate main goalkeepers from regular goalkeepers
            main_gks = [gk for gk in goalkeepers if is_main_goalkeeper(gk)]
            regular_gks = [gk for gk in goalkeepers if not is_main_goalkeeper(gk)]
            
            # Sort main goalkeepers by rating (highest first)
            main_gks.sort(key=lambda x: x.get('overall_rating', 0), reverse=True)
            # Sort regular goalkeepers by rating (highest first)
            regular_gks.sort(key=lambda x: x.get('overall_rating', 0), reverse=True)
            
            # Combine: main goalkeepers first, then regular goalkeepers
            sorted_goalkeepers = main_gks + regular_gks
            
            # Distribute goalkeepers alternately to balance ratings
            for i, gk in enumerate(sorted_goalkeepers):
                rating = gk.get('overall_rating', 0)
                if i % 2 == 0:
                    team_a.append(gk)
                    team_a_rating += rating
                else:
                    team_b.append(gk)
                    team_b_rating += rating
        
        # Remaining players to distribute (goalkeepers if < 2, or all other players if >= 2 goalkeepers)
        if len(goalkeepers) < 2:
            remaining_players = goalkeepers + other_players
        else:
            remaining_players = other_players
        
        # Step 2: Distribute remaining players while balancing ratings and positions
        position_columns = ['central_defender', 'wing_defender', 
                           'central_midfielder', 'wing_midfielder', 'attacker']
        
        for player in remaining_players:
            rating = player.get('overall_rating', 0)
            
            # Calculate position balance - check which team needs each position more
            # Count positions this player has
            player_positions = [pos for pos in position_columns 
                              if player.get(pos) and (str(player.get(pos)).upper().strip() == 'YES' or player.get(pos) is True)]
            
            # Count how many positions favor each team (team with fewer players of that position needs it more)
            team_a_votes = 0
            team_b_votes = 0
            for pos in player_positions:
                count_a = count_position_in_team(team_a, pos)
                count_b = count_position_in_team(team_b, pos)
                if count_a < count_b:
                    team_a_votes += 1  # Team A has fewer of this position
                elif count_b < count_a:
                    team_b_votes += 1  # Team B has fewer of this position
                # If equal, no vote (positions are balanced for this position)
            
            # Calculate rating differences
            rating_diff_if_a = abs((team_a_rating + rating) - team_b_rating)
            rating_diff_if_b = abs(team_a_rating - (team_b_rating + rating))
            
            # Primary factor: rating balance
            # Secondary factor: position balance (when rating difference is small)
            rating_diff_threshold = 10  # If rating difference is less than this, consider positions
            random_threshold = 5  # If rating difference is very small, use randomness
            
            rating_diff = abs(rating_diff_if_a - rating_diff_if_b)
            
            if rating_diff < random_threshold:
                # Rating difference is very small, use randomness for variety
                if random.random() < 0.5:
                    team_a.append(player)
                    team_a_rating += rating
                else:
                    team_b.append(player)
                    team_b_rating += rating
            elif rating_diff < rating_diff_threshold:
                # Rating difference is small, use position balance as tiebreaker
                if team_a_votes > team_b_votes:
                    team_a.append(player)
                    team_a_rating += rating
                elif team_b_votes > team_a_votes:
                    team_b.append(player)
                    team_b_rating += rating
                else:
                    # Positions are equally balanced, use randomness for variety
                    if random.random() < 0.5:
                        team_a.append(player)
                        team_a_rating += rating
                    else:
                        team_b.append(player)
                        team_b_rating += rating
            else:
                # Rating difference is significant, prioritize rating balance
                if rating_diff_if_a <= rating_diff_if_b:
                    team_a.append(player)
                    team_a_rating += rating
                else:
                    team_b.append(player)
                    team_b_rating += rating
        
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
    app.run(debug=True)