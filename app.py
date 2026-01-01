from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
from datetime import datetime
import requests
import io

app = Flask(__name__)

# Google Sheets URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1qv33BjZFsatS1j9M89SysgExFjQ-brUY/export?format=xlsx"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/players')
def get_players():
    try:
        response = requests.get(SHEET_URL)
        response.raise_for_status()
        players_df = pd.read_excel(io.BytesIO(response.content), sheet_name='Players')
        active_players = players_df[players_df['active'] == True].to_dict('records')
        return jsonify(active_players)
    except Exception as e:
        return jsonify({"error": f"Failed to load players: {str(e)}"}), 500

@app.route('/matches')
def get_matches():
    try:
        response = requests.get(SHEET_URL)
        response.raise_for_status()
        matches_df = pd.read_excel(io.BytesIO(response.content), sheet_name='Matches')
        open_matches = matches_df[matches_df['status'] == 'OPEN'].to_dict('records')
        return jsonify(open_matches)
    except Exception as e:
        return jsonify({"error": f"Failed to load matches: {str(e)}"}), 500

@app.route('/generate_teams')
def generate_teams():
    match_id = request.args.get('match_id')
    if not match_id:
        return jsonify({"error": "match_id required"}), 400
    
    try:
        response = requests.get(SHEET_URL)
        response.raise_for_status()
        
        # Get match details
        matches_df = pd.read_excel(io.BytesIO(response.content), sheet_name='Matches')
        match = matches_df[matches_df['match_id'] == int(match_id)].to_dict('records')
        if not match:
            return jsonify({"error": "match not found"}), 404
        match = match[0]
        
        # Get config
        config_df = pd.read_excel(io.BytesIO(response.content), sheet_name='Config')
        config_dict = dict(zip(config_df['key'], config_df['value']))
        
        # Get attending players
        attendance_df = pd.read_excel(io.BytesIO(response.content), sheet_name='Attendance')
        attending_for_match = attendance_df[(attendance_df['match_id'] == int(match_id)) & (attendance_df['attending'] == 'YES')]
        
        players_df = pd.read_excel(io.BytesIO(response.content), sheet_name='Players')
        players_dict = {p['player_id']: p for p in players_df.to_dict('records')}
        
        # Filter players who are both attending the match AND have will_attend_next_match = TRUE
        attending_players = []
        for a in attending_for_match.to_dict('records'):
            if a['player_id'] in players_dict:
                player = players_dict[a['player_id']]
                # Check if player has will_attend_next_match column and it's 'YES' (case insensitive)
                if 'will_attend_next_match' in player and str(player['will_attend_next_match']).upper() == 'YES':
                    attending_players.append(player)
        
        if len(attending_players) < 2:
            return jsonify({"error": "not enough players"}), 400
        
        # Calculate team size: half of attending players, bench if odd
        team_size = len(attending_players) // 2
        
        # Calculate weighted rating
        position_weights = {
            'GK': config_dict.get('GK_WEIGHT', 1.0),
            'DEF': config_dict.get('DEF_WEIGHT', 1.0),
            'MID': config_dict.get('MID_WEIGHT', 1.0),
            'ATT': config_dict.get('ATT_WEIGHT', 1.0)
        }
        
        for p in attending_players:
            pos = p.get('primary_position', 'MID')
            weight = position_weights.get(pos, 1.0)
            p['weighted_rating'] = p['overall_rating'] * weight
        
        # Sort by weighted rating descending
        attending_players.sort(key=lambda x: x['weighted_rating'], reverse=True)
        
        # Select top players for teams (even number)
        selected = attending_players[:2 * team_size]
        
        # Shuffle to randomize team assignment
        import random
        random.shuffle(selected)
        
        # Assign to teams
        team_a = selected[:team_size]
        team_b = selected[team_size:]
        
        # Note if any benched
        benched = attending_players[2 * team_size:] if len(attending_players) > 2 * team_size else []
        
        return jsonify({
            "team_a": [{"name": p['name'], "position": p['primary_position'], "rating": p['overall_rating']} for p in team_a],
            "team_b": [{"name": p['name'], "position": p['primary_position'], "rating": p['overall_rating']} for p in team_b],
            "benched": [{"name": p['name'], "position": p['primary_position'], "rating": p['overall_rating']} for p in benched]
        })
    except Exception as e:
        return jsonify({"error": f"Failed to generate teams: {str(e)}"}), 500
def get_attending_players():
    match_id = request.args.get('match_id')
    if not match_id:
        return jsonify({"error": "match_id required"}), 400
    
    try:
        response = requests.get(SHEET_URL)
        response.raise_for_status()
        
        # Get attending players
        attendance_df = pd.read_excel(io.BytesIO(response.content), sheet_name='Attendance')
        attending_for_match = attendance_df[(attendance_df['match_id'] == int(match_id)) & (attendance_df['attending'] == 'YES')]
        
        players_df = pd.read_excel(io.BytesIO(response.content), sheet_name='Players')
        players_dict = {p['player_id']: p for p in players_df.to_dict('records')}
        
        # Filter players who are both attending the match AND have will_attend_next_match = TRUE
        attending_players = []
        for a in attending_for_match.to_dict('records'):
            if a['player_id'] in players_dict:
                player = players_dict[a['player_id']]
                # Check if player has will_attend_next_match column and it's 'YES' (case insensitive)
                if 'will_attend_next_match' in player and str(player['will_attend_next_match']).upper() == 'YES':
                    attending_players.append(player)
        
        return jsonify([{"name": p['name'], "position": p['primary_position'], "rating": p['overall_rating']} for p in attending_players])
    except Exception as e:
        return jsonify({"error": f"Failed to load attending players: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)