# Football Balanced Teams Generator

A web application for managing football club players, allowing players to vote for attendance, and generating balanced teams based on position, skill, fitness, etc. Uses Google Sheets as the data source.

## Requirements

- **Python 3.12+** (latest stable version recommended)
- Dependencies listed in `requirements.txt`

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

1. **Python Version**: Ensure you have Python 3.12 or later installed
   ```bash
   python --version  # Should show 3.12.x or higher
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   # Or using modern Python packaging:
   pip install .
   ```

3. Create local CSV files with sample data (or use the provided ones):
   - Players.csv
   - Matches.csv
   - Attendance.csv
   - Config.csv

4. Run the app: `python app.py`

5. Open http://localhost:5000 in your browser

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

## Deployment

### Heroku Deployment

1. **Install Heroku CLI** and login:
   ```bash
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   heroku login
   ```

2. **Prepare the app**:
   ```bash
   # Run the deployment script
   deploy.bat
   ```

3. **Create Heroku app**:
   ```bash
   heroku create your-football-teams-app
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   ```

5. **Open your app**:
   ```bash
   heroku open
   ```

### Railway Deployment

1. **Connect to GitHub**: Push your code to GitHub
2. **Create Railway project**: Go to [Railway.app](https://railway.app)
3. **Connect repository**: Link your GitHub repo
4. **Deploy**: Railway will automatically deploy (no environment variables needed)

### Environment Variables

The app automatically detects the `PORT` environment variable set by deployment platforms. No other environment variables are required - users enter their Google Sheets URL directly in the web interface.

## PythonAnywhere Deployment

PythonAnywhere is perfect for hosting Python web applications. Here's how to deploy:

### Quick Setup (Copy Files Method):

1. **Create PythonAnywhere Account**: Sign up at [pythonanywhere.com](https://www.pythonanywhere.com)

2. **Upload Files**: Use the "Files" tab to upload your project files:
   - Upload all files from your project directory
   - Or use git clone if your code is on GitHub

3. **Create Virtual Environment**:
   ```bash
   # In PythonAnywhere bash console
   python3.12 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Create Flask App**:
   - Go to "Web" tab
   - Click "Add a new web app"
   - Choose "Flask" and Python 3.12
   - Set the application path to your main app file

5. **Configure WSGI**:
   - Edit the WSGI configuration file
   - Point it to your Flask app instance

6. **Reload Web App**: Click the green "Reload" button

### Git Method (Recommended for Updates):

1. **Clone Repository**:
   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```

2. **Follow steps 3-6 above**

### PythonAnywhere Benefits:
- ✅ **Python-Native**: Excellent Python support
- ✅ **Persistent Storage**: Your data persists
- ✅ **Easy Scaling**: Upgrade plans available
- ✅ **Console Access**: Full bash access
- ✅ **Free Tier**: Basic usage is free

### Local Production Test

To test production mode locally:

```bash
# Set port (optional, defaults to 5000)
set PORT=8000

# Run in production mode
python app.py
```

## Project Structure

```
football-balanced-teams-generator/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── runtime.txt              # Python version for deployment
├── pyproject.toml           # Modern Python packaging
├── Procfile                 # Heroku process definition
├── README.md                # This file
├── static/
│   ├── app.js              # Frontend JavaScript
│   └── style.css           # Stylesheets
└── templates/
    └── index.html          # Main template
```