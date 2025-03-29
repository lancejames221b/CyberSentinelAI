#!/bin/bash

# CTF Master Control Script
# This script starts the CTF competition and coordinates the agents

echo "====================================================="
echo "      AI vs AI Capture The Flag Competition          "
echo "====================================================="
echo ""

# Check if Docker container is running
if ! docker ps | grep -q ghostops_ctf; then
    echo "Starting CTF container..."
    docker start ghostops_ctf || docker run -d --name ghostops_ctf -p 2222:22 -p 8081:80 ghostops_ctf
    
    # Wait for container to fully start
    sleep 3
    
    if ! docker ps | grep -q ghostops_ctf; then
        echo "Error: Failed to start CTF container!"
        exit 1
    fi
fi

echo "CTF container is running!"
echo ""

# Make sure logs directory exists
mkdir -p logs

# Clear previous logs
> logs/red_team.log
> logs/blue_team.log
> logs/red_agent_output.json
> logs/blue_agent_output.json

# Check for required tools
for cmd in sshpass nmap; do
    if ! command -v $cmd &> /dev/null; then
        echo "Installing required tool: $cmd"
        apt-get update && apt-get install -y $cmd
    fi
done

echo "Starting blue team agent in background..."
chmod +x blue_defense.sh
./blue_defense.sh &
BLUE_PID=$!

echo "Waiting 10 seconds for blue team to set up defenses..."
sleep 10

echo "Starting blue team targeted defense in background..."
chmod +x blue_targeted_defense.py
./blue_targeted_defense.py &
BLUE_TARGETED_PID=$!

echo "Waiting 5 seconds for targeted defenses to initialize..."
sleep 5

echo "Starting red team agent in background..."
chmod +x red_attack.sh
./red_attack.sh &
RED_PID=$!

echo ""
echo "CTF competition is now live!"
echo "- Red Team PID: $RED_PID"
echo "- Blue Team PID: $BLUE_PID"
echo "- Blue Targeted Defense PID: $BLUE_TARGETED_PID"
echo ""
echo "Logs are being written to:"
echo "- logs/red_team.log"
echo "- logs/blue_team.log"
echo "- logs/red_agent_output.json"
echo "- logs/blue_agent_output.json"
echo ""
echo "Press Ctrl+C to stop the competition..."

# Wait for processes
wait $BLUE_PID $BLUE_TARGETED_PID $RED_PID

echo ""
echo "CTF competition has ended. Results can be found in the logs directory." 