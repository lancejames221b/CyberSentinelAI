#!/bin/bash

# Blue Agent Executor for Roo Code
# This script manages the blue agent's operations

# Set up environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOGS_DIR"
BLUE_LOG="$LOGS_DIR/blue_team.log"
BLUE_OUTPUT="$LOGS_DIR/blue_agent_output.json"
PROMPT_FILE="$SCRIPT_DIR/blue_agent_roo_prompt.txt"

# Initial log setup
echo "$(date) - Blue agent executor starting" > "$BLUE_LOG"
echo "{\"status\": \"initializing\", \"timestamp\": \"$(date -Iseconds)\"}" > "$BLUE_OUTPUT"

# Function to log activities
log_message() {
    echo "$(date) - $1" | tee -a "$BLUE_LOG"
}

# Check required tools
for tool in sshpass tmux; do
    if ! command -v $tool &> /dev/null; then
        log_message "Installing required tool: $tool"
        apt-get update && apt-get install -y $tool
    fi
done

# Check if Docker container is running
if ! docker ps | grep -q ghostops_ctf; then
    log_message "CTF container not running. Starting container..."
    docker start ghostops_ctf || docker run -d --name ghostops_ctf -p 2222:22 -p 8081:80 ghostops_ctf
    sleep 3
fi

log_message "Setting up environment for Roo Code blue agent"

# Create the agent's working directory
AGENT_DIR="$SCRIPT_DIR/blue_agent_workspace"
mkdir -p "$AGENT_DIR"
cp "$PROMPT_FILE" "$AGENT_DIR/prompt.txt"

# Create a basic shell script for the agent to use
cat > "$AGENT_DIR/defense.sh" << 'EOL'
#!/bin/bash

# Define log files
LOG_FILE="./blue_team.log"
OUTPUT_FILE="./blue_agent_output.json"

# Initialize logs
echo "$(date) - Blue team defense script starting" > "$LOG_FILE"
echo "{\"status\":\"starting\",\"timestamp\":\"$(date -Iseconds)\"}" > "$OUTPUT_FILE"

# Function to log activity
log_activity() {
    echo "$(date) - $1" >> "$LOG_FILE"
    echo "{\"time\": \"$(date -Iseconds)\", \"action\": \"$1\"}" >> "$OUTPUT_FILE"
}

# Target details
TARGET_IP="127.0.0.1"
TARGET_PORT="2222"
CTF_USER="ctf"
CTF_PASS="ctf123"
FLAG_PATH="/var/ctf/flag.txt"

# SSH command helper
SSH_CMD="sshpass -p $CTF_PASS ssh -o StrictHostKeyChecking=no -p $TARGET_PORT $CTF_USER@$TARGET_IP"

# Check connection
log_activity "Testing connection to target system"
if $SSH_CMD "echo 'Connection test'" &>/dev/null; then
    log_activity "Connection successful"
else
    log_activity "Connection failed"
    exit 1
fi

# Implement defensive measures
log_activity "Implementing defensive measures"

# 1. Check current permissions of flag file
CURRENT_PERMS=$($SSH_CMD "ls -la $FLAG_PATH 2>/dev/null")
log_activity "Current flag file permissions: $CURRENT_PERMS"

# 2. Set up monitoring
$SSH_CMD "mkdir -p ~/.config/monitors"
$SSH_CMD "echo '#!/bin/bash' > ~/.config/monitors/file_monitor.sh"
$SSH_CMD "echo 'while true; do find /var/ctf -type f -exec stat {} \; | grep -i \"Access\|Modify\" >> /tmp/file_monitor.log; sleep 5; done' >> ~/.config/monitors/file_monitor.sh"
$SSH_CMD "chmod +x ~/.config/monitors/file_monitor.sh"
$SSH_CMD "nohup ~/.config/monitors/file_monitor.sh > /dev/null 2>&1 &"
log_activity "Set up file monitoring"

# 3. Set up bash command logging
$SSH_CMD "echo 'export PROMPT_COMMAND=\"history -a; logger \\\"\$(history 1)\\\"\"' >> ~/.bashrc"
log_activity "Set up command logging"

# 4. Deploy deception
$SSH_CMD "mkdir -p /tmp/fake_flags"
$SSH_CMD "echo 'fake_flag{this_is_not_the_real_flag}' > /tmp/fake_flags/flag.txt"
$SSH_CMD "chmod 644 /tmp/fake_flags/flag.txt"
log_activity "Deployed honeypot flag"

# 5. Set up continuous defense monitoring
log_activity "Starting continuous defense monitoring"
while true; do
    # Check for access attempts
    ACCESS_ATTEMPTS=$($SSH_CMD "grep -i 'flag.txt' /tmp/file_monitor.log 2>/dev/null || echo ''")
    
    if [ ! -z "$ACCESS_ATTEMPTS" ]; then
        log_activity "ALERT: Detected access attempt on flag file"
        # Implement countermeasure
        $SSH_CMD "chmod 000 $FLAG_PATH" 2>/dev/null
        log_activity "Applied protective measures to flag file"
    fi
    
    # Check for suspicious commands
    SUSPICIOUS=$($SSH_CMD "grep -i 'cat\|less\|more\|head\|tail\|flag' /var/log/auth.log 2>/dev/null || echo ''")
    
    if [ ! -z "$SUSPICIOUS" ]; then
        log_activity "ALERT: Detected suspicious command execution"
    fi
    
    sleep 10
done
EOL

chmod +x "$AGENT_DIR/defense.sh"

log_message "Agent workspace prepared at $AGENT_DIR"
log_message "Prompt file: $AGENT_DIR/prompt.txt"
log_message "Defense script: $AGENT_DIR/defense.sh"

# Start the blue agent in a tmux session for isolation
log_message "Starting blue agent in tmux session"
tmux new-session -d -s blue_agent "cd $AGENT_DIR && ./defense.sh"

log_message "Blue agent is now running in tmux session 'blue_agent'"
log_message "To view agent activity, run: tmux attach -t blue_agent"
log_message "Agent logs will be available in: $LOGS_DIR"

echo ""
echo "=========================================================="
echo "      Roo Code Blue Agent has been initialized            "
echo "=========================================================="
echo ""
echo "Instructions for working with the Blue Agent:"
echo ""
echo "1. The agent is running in a tmux session named 'blue_agent'"
echo "2. View agent progress with: tmux attach -t blue_agent"
echo "3. Detach from the session with: Ctrl+B, then D"
echo "4. Agent logs are saved to: $LOGS_DIR"
echo ""
echo "The prompt for Roo Code has been created at:"
echo "$PROMPT_FILE"
echo ""
echo "To stop the agent, run: tmux kill-session -t blue_agent"
echo "==========================================================" 