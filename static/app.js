document.addEventListener('DOMContentLoaded', function() {
    const sheetUrlInput = document.getElementById('sheet-url');
    const connectButton = document.getElementById('connect-data');
    const teamGenerationSection = document.getElementById('team-generation-section');
    const teamNameConfigSection = document.getElementById('team-name-config-section');
    
    // Load saved data from cookies
    const savedUrl = getCookie('sheetUrl');
    if (savedUrl) {
        sheetUrlInput.value = savedUrl;
        connectButton.disabled = false;
    }

    // Load saved team names from cookies
    const savedTeam1Name = getCookie('team1Name');
    const savedTeam2Name = getCookie('team2Name');
    if (savedTeam1Name) {
        document.getElementById('team1-name').value = savedTeam1Name;
    }
    if (savedTeam2Name) {
        document.getElementById('team2-name').value = savedTeam2Name;
    }

    // Save team names to cookies when they change
    document.getElementById('team1-name').addEventListener('input', function() {
        setCookie('team1Name', this.value, 30);
    });
    document.getElementById('team2-name').addEventListener('input', function() {
        setCookie('team2Name', this.value, 30);
    });

    // Enable/disable connect button based on URL input
    sheetUrlInput.addEventListener('input', function() {
        connectButton.disabled = !this.value.trim();
    });

    // Handle connect button click
    connectButton.addEventListener('click', connectDataFile);

    // Initially hide team generation section and team name config section
    teamGenerationSection.style.display = 'none';
    teamNameConfigSection.style.display = 'none';
});

function connectDataFile() {
    const sheetUrl = document.getElementById('sheet-url').value.trim();
    const connectButton = document.getElementById('connect-data');
    const teamGenerationSection = document.getElementById('team-generation-section');
    const teamNameConfigSection = document.getElementById('team-name-config-section');
    
    // Disable button and show loading
    connectButton.disabled = true;
    connectButton.textContent = 'Connecting...';
    
    // Load attending players
    loadAttendingPlayers(sheetUrl)
        .then(() => {
            // Success - save URL to cookie and show team generation section and team name config section
            setCookie('sheetUrl', sheetUrl, 30); // Save for 30 days
            teamGenerationSection.style.display = 'block';
            teamNameConfigSection.style.display = 'flex';
            connectButton.textContent = 'Connected!';
            connectButton.style.backgroundColor = '#28a745';
            
            // Add event listener for generate teams button
            document.getElementById('generate-teams').addEventListener('click', () => generateTeams(sheetUrl));
        })
        .catch((error) => {
            // Error - reset button and hide team name config section
            connectButton.disabled = false;
            connectButton.textContent = 'Connect Data File';
            teamNameConfigSection.style.display = 'none';
            alert('Failed to connect to data file: ' + error);
        });
}

function loadAttendingPlayers(sheetUrl) {
    return fetch(`/attending_players?url=${encodeURIComponent(sheetUrl)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to load attending players');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            showAttendingPlayers(data);
        });
}

function generateTeams(sheetUrl) {
    const button = document.getElementById('generate-teams');
    const attendingDiv = document.getElementById('attending-players');
    const teamsContainer = document.getElementById('teams-container');
    
    // Disable button
    button.disabled = true;
    button.textContent = 'Generating...';
    
    
    fetch(`/generate_teams?url=${encodeURIComponent(sheetUrl)}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                resetUI();
                return;
            }
            
            // Show attending players
            const allPlayers = [...data.team_a, ...data.team_b];
            // Note: Attending players are already displayed from connectDataFile, don't reload them
            
            // Get team names from input boxes
            const team1Name = document.getElementById('team1-name').value.trim() || 'Team 1';
            const team2Name = document.getElementById('team2-name').value.trim() || 'Team 2';
            
            // Initialize team headers with total rating only
            document.querySelector('#team-a h3').textContent = `${team1Name} (Total: 0.0)`;
            document.querySelector('#team-b h3').textContent = `${team2Name} (Total: 0.0)`;
            
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

    // Update header with player count
    const header = attendingDiv.querySelector('h4');
    header.textContent = `Attending Players (${players.length})`;

    const playersContainer = attendingDiv.querySelector('.attending-players');
    // Clear existing bubbles first
    playersContainer.innerHTML = '';
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

    // Show teams container
    teamsContainer.style.display = 'flex';

    // Calculate center positions of team cards relative to attending players
    const attendingRect = attendingDiv.getBoundingClientRect();
    const teamARect = document.getElementById('team-a').getBoundingClientRect();
    const teamBRect = document.getElementById('team-b').getBoundingClientRect();

    // Calculate positions relative to the viewport
    const attendingCenterX = attendingRect.left + attendingRect.width / 2;
    const teamACenterX = teamARect.left + teamARect.width / 2;
    const teamBCenterX = teamBRect.left + teamBRect.width / 2;

    const teamAOffset = teamACenterX - attendingCenterX;
    const teamBOffset = teamBCenterX - attendingCenterX;

    // Debug logging
    console.log('Attending center X:', attendingCenterX);
    console.log('Team A center X:', teamACenterX, 'Offset:', teamAOffset);
    console.log('Team B center X:', teamBCenterX, 'Offset:', teamBOffset);

    // Get team names from input boxes
    const team1Name = document.getElementById('team1-name').value.trim() || 'Team 1';
    const team2Name = document.getElementById('team2-name').value.trim() || 'Team 2';

    // Get all bubbles
    const allBubbles = Array.from(attendingDiv.querySelectorAll('.player-bubble'));
    const remainingBubbles = [...allBubbles];

    // Track current team stats
    let teamAStats = { count: 0, total: 0 };
    let teamBStats = { count: 0, total: 0 };
    
    function animateRandom() {
        if (remainingBubbles.length === 0) {
            // All done - update button text and keep it disabled
            const button = document.getElementById('generate-teams');
            button.textContent = 'Generated';
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

        // Calculate bubble's current position relative to attending center
        const bubbleRect = bubble.getBoundingClientRect();
        const bubbleCenterX = bubbleRect.left + bubbleRect.width / 2;
        const bubbleOffsetFromAttending = bubbleCenterX - attendingCenterX;

        if (data.team_a.some(p => p.name === playerName)) {
            // Move from bubble's current position to team A center
            targetX = (teamAOffset - bubbleOffsetFromAttending) + 'px';
            targetTeam = 'team-a-players';
            playerData = data.team_a.find(p => p.name === playerName);
        } else if (data.team_b.some(p => p.name === playerName)) {
            // Move from bubble's current position to team B center
            targetX = (teamBOffset - bubbleOffsetFromAttending) + 'px';
            targetTeam = 'team-b-players';
            playerData = data.team_b.find(p => p.name === playerName);
        }

        // Debug logging
        console.log('Bubble offset from attending:', bubbleOffsetFromAttending, 'Target X:', targetX);

        // Set random intermediate position for more interesting animation
        const randomX = (Math.random() - 0.5) * 400; // Random between -200 and 200
        bubble.style.setProperty('--random-x', randomX + 'px');

        // Set the target position
        bubble.style.setProperty('--target-x', targetX);
        bubble.classList.add('moving');
        
        // After animation, add to team and continue
        setTimeout(() => {
            if (targetTeam && playerData) {
                // Update stats for team players
                if (targetTeam === 'team-a-players') {
                    teamAStats.count++;
                    teamAStats.total += playerData.rating;
                    const playerCard = document.createElement('div');
                    playerCard.className = 'player-card';
                    playerCard.textContent = `${teamAStats.count}. ${playerData.name} (${playerData.position}) - ${playerData.rating}`;
                    document.getElementById(targetTeam).appendChild(playerCard);
                    document.querySelector('#team-a h3').textContent = `${team1Name} (Total: ${teamAStats.total.toFixed(1)})`;
                } else if (targetTeam === 'team-b-players') {
                    teamBStats.count++;
                    teamBStats.total += playerData.rating;
                    const playerCard = document.createElement('div');
                    playerCard.className = 'player-card';
                    playerCard.textContent = `${teamBStats.count}. ${playerData.name} (${playerData.position}) - ${playerData.rating}`;
                    document.getElementById(targetTeam).appendChild(playerCard);
                    document.querySelector('#team-b h3').textContent = `${team2Name} (Total: ${teamBStats.total.toFixed(1)})`;
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

// Cookie utility functions
function setCookie(name, value, days) {
    const expires = new Date();
    expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
    document.cookie = name + '=' + encodeURIComponent(value) + ';expires=' + expires.toUTCString() + ';path=/';
}

function getCookie(name) {
    const nameEQ = name + '=';
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return decodeURIComponent(c.substring(nameEQ.length, c.length));
    }
    return null;
}