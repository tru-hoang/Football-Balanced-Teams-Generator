# Football Balanced Teams Generator

A web application for managing football club players, allowing players to vote for attendance, and generating balanced teams based on position, skill, fitness, etc. Uses Google Sheets as the data source.

## Features

- Player management (via Google Sheets)
- Attendance voting for matches
- Balanced team generation based on position, skill, fitness
- Google Sheets integration for easy admin and data management

## Spreadsheet Structure

Create a Google Spreadsheet named "Football Club Data" with the following tabs:

1. **Players**: Master list of players (admin-only)
   - Columns: player_id, name, primary_position, secondary_position, skill, fitness, experience, overall_rating, active

2. **Matches**: Upcoming and past matches (admin-only)
   - Columns: match_id, date, location, players_per_team, status (OPEN/CLOSED)

3. **Attendance**: Player votes
   - Columns: match_id, player_id, attending (YES/NO), timestamp

4. **Config**: Balancing parameters (admin-only)
   - Columns: key, value
   - Examples: GK_WEIGHT, 1.2; DEF_WEIGHT, 1.0; etc.

5. **Teams**: Generated teams (read-only)
   - Columns: Team, Player, Position, Rating

## Setup

1. Install dependencies: `pip install -r requirements.txt`

2. Create local CSV files with sample data (or use the provided ones):
   - Players.csv
   - Matches.csv
   - Attendance.csv
   - Config.csv

3. Run the app: `python app.py`

4. Open http://localhost:5000 in your browser

## Local Development

The app reads from a local Excel file `data.xlsx` with multiple sheets for faster development. Sample data is provided. Voting does not persist locally.

## Spreadsheet Structure

Create `data.xlsx` with the following sheets:

1. **Players**: Master list of players
   - Columns: player_id, name, primary_position, secondary_position, skill, fitness, experience, overall_rating, active

2. **Matches**: Upcoming and past matches
   - Columns: match_id, date, location, status (OPEN/CLOSED)
   - Note: Team sizes are automatically calculated as half of attending players

3. **Attendance**: Player attendance votes
   - Columns: match_id, player_id, attending (YES/NO), timestamp

4. **Config**: Balancing parameters
   - Columns: key, value
   - Examples: GK_WEIGHT, 1.2; DEF_WEIGHT, 1.0; etc.

5. **Teams**: Generated teams (output)
   - Columns: Team, Player, Position, Rating

## Usage

- Admins edit player and match data in Google Sheets or local CSVs
- Players vote for attendance directly in the Google Sheets Attendance tab
- Admins generate balanced teams using the web app