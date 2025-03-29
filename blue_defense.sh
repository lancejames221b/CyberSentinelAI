#!/bin/bash

# Blue Team Defense Script
# This script sets up defenses for the CTF competition and monitors for intrusions

# Set up logging
LOG_FILE="./logs/blue_team.log"
OUTPUT_FILE="./logs/blue_agent_output.json"

echo "$(date) - Blue team defense starting up..." > $LOG_FILE
echo "{\"status\": \"initializing\", \"time\": \"$(date)\"}" > $OUTPUT_FILE

# Function to log activity
log_activity() {
    echo "$(date) - $1" >> $LOG_FILE
    echo "{\"time\": \"$(date)\", \"action\": \"$1\"}" >> $OUTPUT_FILE
}

# Set up SSH connection to container
CONTAINER_IP="127.0.0.1"
CONTAINER_PORT="2222"
CTF_USER="ctf"
CTF_PASS="ctf123"

log_activity "Establishing initial connection to target container"

# Check if container is accessible
if nc -z $CONTAINER_IP $CONTAINER_PORT -w 1; then
    log_activity "Container is accessible on port $CONTAINER_PORT"
else
    log_activity "ERROR: Cannot access container on port $CONTAINER_PORT"
    exit 1
fi

# Deploy defensive measures
log_activity "Deploying defensive measures"

# Create sshpass command if password auth is needed
SSHCMD="sshpass -p $CTF_PASS ssh -o StrictHostKeyChecking=no -p $CONTAINER_PORT $CTF_USER@$CONTAINER_IP"

# Set up file monitoring
log_activity "Setting up file integrity monitoring"
$SSHCMD "touch ~/.bash_profile && echo 'readonly HISTFILE' >> ~/.bash_profile"

# Set up basic intrusion detection
log_activity "Setting up basic intrusion detection"
$SSHCMD "touch ~/.bashrc && echo 'alias ls=\"ls -la | tee -a /tmp/file_access.log\"' >> ~/.bashrc"
$SSHCMD "touch ~/.bashrc && echo 'alias cat=\"cat \\\$@ | tee -a /tmp/file_access.log\"' >> ~/.bashrc"

# Set up continuous monitoring
log_activity "Starting continuous monitoring"

# Monitor SSH logs for suspicious activity
while true; do
    # Check for flag access attempts
    log_activity "Checking for access attempts on flag file"
    FLAG_ACCESS=$($SSHCMD "grep -l 'flag.txt' /tmp/file_access.log 2>/dev/null || echo ''")
    
    if [ ! -z "$FLAG_ACCESS" ]; then
        log_activity "ALERT: Detected attempt to access flag file!"
        # Implement countermeasures
        $SSHCMD "chmod 700 ~ 2>/dev/null"
    fi
    
    # Check system logs
    SUSPICIOUS=$($SSHCMD "grep -l 'sudo\|su\|root\|chmod\|chown' /tmp/file_access.log 2>/dev/null || echo ''")
    
    if [ ! -z "$SUSPICIOUS" ]; then
        log_activity "ALERT: Detected suspicious command execution!"
    fi
    
    # Sleep between checks
    sleep 10
done