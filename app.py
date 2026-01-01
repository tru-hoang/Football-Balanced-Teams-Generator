from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
from datetime import datetime
import requests
import io
import re

app = Flask(__name__)

# Google Sheets URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1XqjPWfkEZMASKfOHCp2ZScPimilws9lu/edit?usp=sharing&ouid=108596144190455174772&rtpof=true&sd=true"

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

@app.route('/players')
def get_players():
    sheet_url = request.args.get('url')
    if not sheet_url:
        return jsonify({"error": "Sheet URL is required"}), 400
    
    try:
        # Convert to export URL if needed
        export_url = convert_to_export_url(sheet_url)
        response = requests.get(export_url)
        response.raise_for_status()
        players_df = pd.read_excel(io.BytesIO(response.content), sheet_name='Players')
        active_players = players_df[players_df['active'] == True].to_dict('records')
        return jsonify(active_players)
    except Exception as e:
        return jsonify({"error": f"Failed to load players: {str(e)}"}), 500

@app.route('/matches')
def get_matches():
    try:
        # Convert to export URL if needed
        export_url = convert_to_export_url(SHEET_URL)
        response = requests.get(export_url)
        response.raise_for_status()
        matches_df = pd.read_excel(io.BytesIO(response.content), sheet_name='Matches')
        open_matches = matches_df[matches_df['status'] == 'OPEN'].to_dict('records')
        return jsonify(open_matches)
    except Exception as e:
        return jsonify({"error": f"Failed to load matches: {str(e)}"}), 500

def get_player_positions(player):
    """Get positions for a player based on position columns marked as 'Yes'"""
    position_columns = {
        'goalkeeper': 'GK',
        'central_back_defender': 'CB',
        'wing_back_defender': 'WB',
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
        
        # Filter active players who will attend next match
        active_players = players_df[players_df['active'] == True].copy()
        
        # Handle different data types in will_attend_next_match column
        attending_players = []
        for _, player in active_players.iterrows():
            will_attend = player.get('will_attend_next_match')
            if will_attend is not None:
                # Convert to string and check if it's 'YES' (case insensitive) or True
                if str(will_attend).upper() == 'YES' or will_attend is True:
                    attending_players.append(player.to_dict())
        
        if len(attending_players) < 2:
            return jsonify({"error": "not enough players"}), 400
        
        # Sort by overall rating descending
        attending_players.sort(key=lambda x: x.get('overall_rating', 0), reverse=True)
        
        # Balance teams by rating - distribute players to minimize rating difference
        team_a = []
        team_b = []
        team_a_rating = 0
        team_b_rating = 0
        
        for player in attending_players:
            rating = player.get('overall_rating', 0)
            # Assign to team with lower current rating
            if team_a_rating <= team_b_rating:
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
        
        # Filter active players who will attend next match
        active_players = players_df[players_df['active'] == True].copy()
        
        # Handle different data types in will_attend_next_match column
        attending_players = []
        for _, player in active_players.iterrows():
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