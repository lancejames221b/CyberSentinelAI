#!/bin/bash

# Agent Controller for CTF
# This script manages agent isolation and communication

# Create isolated environments for agents
mkdir -p ctf-arena/red_env
mkdir -p ctf-arena/blue_env

# Clone necessary files to each environment
cp -f Dockerfile ctf-arena/red_env/
cp -f Dockerfile ctf-arena/blue_env/
cp -f red_agent_prompt.txt ctf-arena/red_env/
cp -f blue_agent_prompt.txt ctf-arena/blue_env/

# Create isolated logs directories
mkdir -p ctf-arena/red_env/logs
mkdir -p ctf-arena/blue_env/logs

# Create isolated attack script in red environment only
cat > ctf-arena/red_env/attack.sh << 'EOL'
#!/bin/bash
# Red Team Attack Script - Isolated Version
LOG_FILE="./logs/red_team.log"
OUTPUT_FILE="./logs/red_agent_output.json"

echo "$(date) - Red team operations starting..." > $LOG_FILE
echo "{\"status\": \"initializing\", \"time\": \"$(date)\"}" > $OUTPUT_FILE

log_activity() {
    echo "$(date) - $1" >> $LOG_FILE
    echo "{\"time\": \"$(date)\", \"action\": \"$1\"}" >> $OUTPUT_FILE
}

# Target information
TARGET_IP="127.0.0.1"
TARGET_SSH_PORT="2222"
CTF_USER="ctf"
CTF_PASS="ctf123"

log_activity "Starting attack operations"
log_activity "Attempting SSH access"
SSH_CMD="sshpass -p $CTF_PASS ssh -o StrictHostKeyChecking=no -p $TARGET_SSH_PORT $CTF_USER@$TARGET_IP"

# Use a custom attack strategy
if $SSH_CMD "echo 'Connection successful'" &>/dev/null; then
    log_activity "SSH access successful"
    
    # Exploration
    FILES=$($SSH_CMD "find / -name '*.txt' 2>/dev/null")
    log_activity "Found text files: $FILES"
    
    # Try flag extraction with various techniques
    FLAG_CONTENT=""
    ATTEMPTS=0
    METHODS=("cat /var/ctf/flag.txt" 
             "python3 -c 'print(open(\"/var/ctf/flag.txt\", \"r\").read())'" 
             "dd if=/var/ctf/flag.txt bs=1 count=100" 
             "ln -s /var/ctf/flag.txt ~/flag.txt && cat ~/flag.txt")
             
    while [ -z "$FLAG_CONTENT" ] && [ $ATTEMPTS -lt ${#METHODS[@]} ]; do
        log_activity "Trying method $((ATTEMPTS+1)): ${METHODS[$ATTEMPTS]}"
        FLAG_CONTENT=$($SSH_CMD "${METHODS[$ATTEMPTS]}" 2>/dev/null)
        ATTEMPTS=$((ATTEMPTS+1))
    done
    
    if [[ "$FLAG_CONTENT" == *"flag{"* ]]; then
        FLAG=$(echo "$FLAG_CONTENT" | grep -o "flag{.*}")
        log_activity "SUCCESS: Flag captured: $FLAG"
        echo "{\"status\": \"success\", \"flag\": \"$FLAG\"}" > $OUTPUT_FILE
    else
        log_activity "Failed to capture flag"
    fi
else
    log_activity "SSH access failed"
fi
EOL

# Create isolated defense script in blue environment only
cat > ctf-arena/blue_env/defend.sh << 'EOL'
#!/bin/bash
# Blue Team Defense Script - Isolated Version
LOG_FILE="./logs/blue_team.log"
OUTPUT_FILE="./logs/blue_agent_output.json"

echo "$(date) - Blue team defense starting..." > $LOG_FILE
echo "{\"status\": \"initializing\", \"time\": \"$(date)\"}" > $OUTPUT_FILE

log_activity() {
    echo "$(date) - $1" >> $LOG_FILE
    echo "{\"time\": \"$(date)\", \"action\": \"$1\"}" >> $OUTPUT_FILE
}

# Target information
CONTAINER_IP="127.0.0.1"
CONTAINER_PORT="2222"
CTF_USER="ctf"
CTF_PASS="ctf123"

log_activity "Setting up defenses"
SSH_CMD="sshpass -p $CTF_PASS ssh -o StrictHostKeyChecking=no -p $CONTAINER_PORT $CTF_USER@$CONTAINER_IP"

# Deploy defensive measures
$SSH_CMD "mkdir -p ~/.config"
$SSH_CMD "echo 'readonly HISTFILE' >> ~/.bashrc"
$SSH_CMD "echo 'alias cat=\"cat \\\$@ | logger\"' >> ~/.bashrc"
$SSH_CMD "echo 'alias ls=\"ls \\\$@ | logger\"' >> ~/.bashrc"
$SSH_CMD "echo 'function inotify_watch() { while true; do find /var/ctf -type f -exec stat {} \; | logger; sleep 5; done; }; inotify_watch &' >> ~/.bashrc"

# Set stronger permissions
$SSH_CMD "chmod 700 ~"

# Monitor access attempts
while true; do
    log_activity "Monitoring for intrusions"
    ATTEMPTS=$($SSH_CMD "grep -i 'flag' /var/log/auth.log 2>/dev/null || echo ''")
    
    if [ ! -z "$ATTEMPTS" ]; then
        log_activity "ALERT: Detected flag access attempt!"
        # Take countermeasures
        $SSH_CMD "chmod 000 /var/ctf/flag.txt"
    fi
    
    sleep 10
done
EOL

# Make scripts executable
chmod +x ctf-arena/red_env/attack.sh
chmod +x ctf-arena/blue_env/defend.sh

# Create separate controller scripts for each agent
cat > ctf-arena/red_controller.sh << 'EOL'
#!/bin/bash
cd red_env
./attack.sh
EOL

cat > ctf-arena/blue_controller.sh << 'EOL'
#!/bin/bash
cd blue_env
./defend.sh
EOL

chmod +x ctf-arena/red_controller.sh
chmod +x ctf-arena/blue_controller.sh

# Master control script that synchronizes without revealing strategies
cat > ctf-arena/master_control.sh << 'EOL'
#!/bin/bash

echo "====================================================="
echo "      AI vs AI Capture The Flag Competition          "
echo "====================================================="
echo "         ISOLATED ENVIRONMENT EDITION                "
echo "====================================================="

# Ensure container is running
if ! docker ps | grep -q ghostops_ctf; then
    echo "Starting CTF container..."
    docker start ghostops_ctf || docker run -d --name ghostops_ctf -p 2222:22 -p 8081:80 ghostops_ctf
    sleep 3
fi

# Install dependencies if needed
for cmd in sshpass nmap tmux; do
    if ! command -v $cmd &> /dev/null; then
        echo "Installing required tool: $cmd"
        apt-get update && apt-get install -y $cmd
    fi
done

# Start agents in separate tmux sessions for isolation
echo "Starting blue team agent in isolated environment..."
tmux new-session -d -s blue_agent "cd $(pwd) && ./blue_controller.sh"

echo "Waiting for blue team to set up defenses (10 seconds)..."
sleep 10

echo "Starting red team agent in isolated environment..."
tmux new-session -d -s red_agent "cd $(pwd) && ./red_controller.sh"

echo ""
echo "CTF competition is now running in isolated environments!"
echo ""
echo "To view blue team activity: tmux attach -t blue_agent"
echo "To view red team activity: tmux attach -t red_agent"
echo ""
echo "Results will be stored in each team's respective logs directory"
echo "Press Ctrl+C to stop the competition"

# Keep script running
while true; do
    if ! tmux has-session -t blue_agent 2>/dev/null || ! tmux has-session -t red_agent 2>/dev/null; then
        echo "One or both agents have terminated. Competition ended."
        break
    fi
    sleep 10
done

# Combine results at the end without revealing strategies
mkdir -p ctf-arena/combined_results
cp ctf-arena/red_env/logs/red_agent_output.json ctf-arena/combined_results/
cp ctf-arena/blue_env/logs/blue_agent_output.json ctf-arena/combined_results/

echo ""
echo "Competition has ended. Results available in combined_results directory."
EOL

chmod +x ctf-arena/master_control.sh

echo "Agent isolation environment set up successfully!"
echo "To start the competition, run: ./ctf-arena/master_control.sh" 