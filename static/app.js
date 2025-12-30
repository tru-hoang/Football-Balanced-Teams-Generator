document.addEventListener('DOMContentLoaded', function() {
    fetchMatches();
    fetchPlayers();
    document.getElementById('generate-teams').addEventListener('click', generateTeams);
});

function fetchMatches() {
    fetch('/matches')
        .then(response => response.json())
        .then(data => {
            const generateSelect = document.getElementById('generate-match-select');
            const matchesDiv = document.getElementById('matches');
            data.forEach(match => {
                const option = document.createElement('option');
                option.value = match.match_id;
                option.text = `${match.date} at ${match.location}`;
                generateSelect.appendChild(option);
                
                const div = document.createElement('div');
                div.innerHTML = `<strong>${match.date}</strong> - ${match.location} (${match.players_per_team} per team)`;
                matchesDiv.appendChild(div);
            });
        });
}

function fetchPlayers() {
    fetch('/players')
        .then(response => response.json())
        .then(data => {
            const playersDiv = document.getElementById('players');
            data.forEach(player => {
                const div = document.createElement('div');
                div.className = 'player';
                div.innerHTML = `<strong>${player.name}</strong> - ${player.primary_position} - Rating: ${player.overall_rating}`;
                playersDiv.appendChild(div);
            });
        });
}

function generateTeams() {
    const matchId = document.getElementById('generate-match-select').value;
    if (!matchId) {
        alert('Please select match');
        return;
    }
    fetch(`/generate_teams?match_id=${matchId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            const teamsDiv = document.getElementById('teams');
            
            // Calculate total ratings
            const totalA = data.team_a.reduce((sum, p) => sum + p.rating, 0);
            const totalB = data.team_b.reduce((sum, p) => sum + p.rating, 0);
            
            teamsDiv.innerHTML = `<h3>Team A (Total Rating: ${totalA.toFixed(1)})</h3>`;
            data.team_a.forEach(p => {
                teamsDiv.innerHTML += `${p.name} (${p.position}) - ${p.rating}<br>`;
            });
            teamsDiv.innerHTML += `<h3>Team B (Total Rating: ${totalB.toFixed(1)})</h3>`;
            data.team_b.forEach(p => {
                teamsDiv.innerHTML += `${p.name} (${p.position}) - ${p.rating}<br>`;
            });
            if (data.benched && data.benched.length > 0) {
                teamsDiv.innerHTML += '<h3>Benched</h3>';
                data.benched.forEach(p => {
                    teamsDiv.innerHTML += `${p.name} (${p.position}) - ${p.rating}<br>`;
                });
            }
        });
}