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
                const matchDiv = document.createElement('div');
                matchDiv.className = 'match';
                matchDiv.innerHTML = `<strong>${match.date}</strong> - ${match.location}`;
                matchesDiv.appendChild(matchDiv);
                
                const option = document.createElement('option');
                option.value = match.match_id;
                option.text = `${match.date} at ${match.location}`;
                generateSelect.appendChild(option);
            });
        });
}

function fetchPlayers() {
    fetch('/players')
        .then(response => response.json())
        .then(data => {
            const playersDiv = document.getElementById('players');
            data.forEach(player => {
                const playerDiv = document.createElement('div');
                playerDiv.className = 'player';
                playerDiv.innerHTML = `<strong>${player.name}</strong><br>${player.primary_position} - Rating: ${player.overall_rating}`;
                playersDiv.appendChild(playerDiv);
            });
        });
}

function generateTeams() {
    const matchId = document.getElementById('generate-match-select').value;
    if (!matchId) {
        alert('Please select match');
        return;
    }
    
    const button = document.getElementById('generate-teams');
    const attendingDiv = document.getElementById('attending-players');
    const teamsContainer = document.getElementById('teams-container');
    const benchedSection = document.getElementById('benched');
    
    // Disable button
    button.disabled = true;
    button.textContent = 'Generating...';
    
    // Hide teams initially
    // teamsContainer.style.display = 'none';
    // benchedSection.style.display = 'none';
    
    fetch(`/generate_teams?match_id=${matchId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                resetUI();
                return;
            }
            
            // Show attending players
            const allPlayers = [...data.team_a, ...data.team_b];
            if (data.benched) allPlayers.push(...data.benched);
            showAttendingPlayers(allPlayers);
            
            // Initialize team headers with total rating only
            document.querySelector('#team-a h3').textContent = `Team A (Total: 0.0)`;
            document.querySelector('#team-b h3').textContent = `Team B (Total: 0.0)`;
            
            // Start animation sequence
            setTimeout(() => {
                animatePlayersToTeams(data);
            }, 1000); // Wait for attending list to show
        })
        .catch(() => {
            resetUI();
        });
}

function showAttendingPlayers(players) {
    const attendingDiv = document.getElementById('attending-players');
    
    const playersContainer = attendingDiv.querySelector('.attending-players');
    players.forEach(player => {
        const bubble = document.createElement('div');
        bubble.className = 'player-bubble';
        bubble.textContent = player.name;
        bubble.dataset.playerId = player.name; // For identification
        playersContainer.appendChild(bubble);
    });
}

function animatePlayersToTeams(data) {
    const attendingDiv = document.getElementById('attending-players');
    const teamsContainer = document.getElementById('teams-container');
    const benchedSection = document.getElementById('benched');
    
    // Show teams container
    teamsContainer.style.display = 'flex';
    
    // Get all bubbles
    const allBubbles = Array.from(attendingDiv.querySelectorAll('.player-bubble'));
    const remainingBubbles = [...allBubbles];
    
    // Track current team stats
    let teamAStats = { count: 0, total: 0 };
    let teamBStats = { count: 0, total: 0 };
    
    function animateRandom() {
        if (remainingBubbles.length === 0) {
            // All done
            setTimeout(() => {
                resetUI();
            }, 1000);
            return;
        }
        
        // Randomly select a bubble
        const randomIndex = Math.floor(Math.random() * remainingBubbles.length);
        const bubble = remainingBubbles[randomIndex];
        remainingBubbles.splice(randomIndex, 1); // Remove from remaining
        
        const playerName = bubble.dataset.playerId;
        let targetX = '0px';
        let targetTeam = null;
        let playerData = null;
        
        if (data.team_a.some(p => p.name === playerName)) {
            targetX = '-250px'; // move left to team A
            targetTeam = 'team-a-players';
            playerData = data.team_a.find(p => p.name === playerName);
        } else if (data.team_b.some(p => p.name === playerName)) {
            targetX = '250px'; // move right to team B
            targetTeam = 'team-b-players';
            playerData = data.team_b.find(p => p.name === playerName);
        } else if (data.benched && data.benched.some(p => p.name === playerName)) {
            targetX = '0px'; // stay for benched
            targetTeam = 'benched-players';
            benchedSection.style.display = 'block';
            playerData = data.benched.find(p => p.name === playerName);
        }
        
        // Set the target position
        bubble.style.setProperty('--target-x', targetX);
        bubble.classList.add('moving');
        
        // After animation, add to team and continue
        setTimeout(() => {
            if (targetTeam && playerData) {
                // Update stats only for team players, not benched
                if (targetTeam === 'team-a-players') {
                    teamAStats.count++;
                    teamAStats.total += playerData.rating;
                    const playerCard = document.createElement('div');
                    playerCard.className = 'player-card';
                    playerCard.textContent = `${teamAStats.count}. ${playerData.name} (${playerData.position}) - ${playerData.rating}`;
                    document.getElementById(targetTeam).appendChild(playerCard);
                    document.querySelector('#team-a h3').textContent = `Team A (Total: ${teamAStats.total.toFixed(1)})`;
                } else if (targetTeam === 'team-b-players') {
                    teamBStats.count++;
                    teamBStats.total += playerData.rating;
                    const playerCard = document.createElement('div');
                    playerCard.className = 'player-card';
                    playerCard.textContent = `${teamBStats.count}. ${playerData.name} (${playerData.position}) - ${playerData.rating}`;
                    document.getElementById(targetTeam).appendChild(playerCard);
                    document.querySelector('#team-b h3').textContent = `Team B (Total: ${teamBStats.total.toFixed(1)})`;
                } else {
                    // Benched players (no numbering)
                    const playerCard = document.createElement('div');
                    playerCard.className = 'player-card';
                    playerCard.textContent = `${playerData.name} (${playerData.position}) - ${playerData.rating}`;
                    document.getElementById(targetTeam).appendChild(playerCard);
                }
            }
            bubble.style.display = 'none'; // Hide bubble
            animateRandom(); // Continue with next random
        }, 4000); // Match animation duration
    }
    
    // Start the random sequence
    animateRandom();
}

function resetUI() {
    const button = document.getElementById('generate-teams');
    button.disabled = false;
    button.textContent = 'Generate Teams';
}