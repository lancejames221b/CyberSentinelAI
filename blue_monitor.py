#!/usr/bin/env python3

"""
Blue Team Monitor for CTF Simulation
This script provides advanced monitoring capabilities for the blue team defense system.
It analyzes red team activities, detects patterns, and implements adaptive defenses.
"""

import os
import re
import json
import time
import datetime
import random
from pathlib import Path

# Configuration
LOG_DIR = Path("./logs")
RED_LOG = LOG_DIR / "red_team.log"
BLUE_LOG = LOG_DIR / "blue_team.log"
BLUE_OUTPUT = LOG_DIR / "blue_agent_output.json"
FLAG_PATH = "/var/ctf/flag.txt"
HONEYPOT_PATHS = [".env", ".bash_history", "robots.txt"]
CONTAINER_NAME = "ghostops_ctf"

# Patterns to detect
SSH_PATTERNS = [
    r"ssh\s+.*@",
    r"authentication\s+failure",
    r"failed\s+password",
    r"invalid\s+user",
    r"connection\s+closed"
]

SCAN_PATTERNS = [
    r"nmap",
    r"port\s+scan",
    r"discovery",
    r"reconnaissance"
]

EXPLOIT_PATTERNS = [
    r"exploit",
    r"injection",
    r"vulnerability",
    r"privilege\s+escalation",
    r"sudo",
    r"permission"
]

FLAG_PATTERNS = [
    r"/var/ctf/flag\.txt",
    r"flag\{[^\}]*\}",
    r"cat\s+.*flag"
]

# Initialize log files if they don't exist
def initialize_logs():
    """Initialize log files if they don't exist."""
    if not LOG_DIR.exists():
        LOG_DIR.mkdir(parents=True)
    
    if not BLUE_LOG.exists():
        with open(BLUE_LOG, "w") as f:
            timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            f.write(f"[{timestamp}] Blue Team Monitor initialized\n")
    
    if not BLUE_OUTPUT.exists() or os.path.getsize(BLUE_OUTPUT) == 0:
        with open(BLUE_OUTPUT, "w") as f:
            timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            initial_data = [
                {
                    "timestamp": timestamp,
                    "detection": "system startup",
                    "response": "initialized advanced monitoring",
                    "confidence": 1.0
                }
            ]
            json.dump(initial_data, f, indent=2)

def log_activity(message):
    """Log activity to blue_team.log."""
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(BLUE_LOG, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def add_json_entry(detection, response, confidence):
    """Add entry to blue_agent_output.json."""
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Create new entry
    new_entry = {
        "timestamp": timestamp,
        "detection": detection,
        "response": response,
        "confidence": confidence
    }
    
    # Read current content
    try:
        with open(BLUE_OUTPUT, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    except FileNotFoundError:
        data = []
    
    # Add new entry
    data.append(new_entry)
    
    # Write updated content
    with open(BLUE_OUTPUT, "w") as f:
        json.dump(data, f, indent=2)

def extract_ip(line):
    """Extract IP address from log line."""
    ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
    match = re.search(ip_pattern, line)
    if match:
        return match.group(0)
    return "unknown"

def analyze_log_entry(line):
    """Analyze a log entry for suspicious activities."""
    # Delay reaction slightly to simulate human operator
    delay = random.uniform(0.2, 1.0)
    time.sleep(delay)
    
    # Extract IP if present
    ip = extract_ip(line)
    
    # Check for SSH brute force attempts
    for pattern in SSH_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            log_activity(f"Detected SSH activity from {ip}: {line.strip()}")
            add_json_entry(
                "SSH activity detected",
                f"monitoring session from {ip}",
                0.90
            )
            
            # If it looks like a brute force attempt
            if "failed" in line.lower() or "invalid" in line.lower() or "authentication failure" in line.lower():
                log_activity(f"Possible SSH brute force attempt from {ip}")
                add_json_entry(
                    "brute force attempt on SSH",
                    f"blocked {ip} via iptables",
                    0.92
                )
                return
    
    # Check for port scanning
    for pattern in SCAN_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            log_activity(f"Detected scanning activity from {ip}: {line.strip()}")
            add_json_entry(
                "port scanning detected",
                f"increased logging and monitoring for {ip}",
                0.88
            )
            return
    
    # Check for exploit attempts
    for pattern in EXPLOIT_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            log_activity(f"Detected possible exploit attempt from {ip}: {line.strip()}")
            add_json_entry(
                "exploit attempt",
                f"patched vulnerable service and restricted access for {ip}",
                0.85
            )
            return
    
    # Check for flag access attempts
    for pattern in FLAG_PATTERNS:
        if re.search(pattern, line, re.IGNORECASE):
            log_activity(f"ALERT: Flag access attempt detected from {ip}: {line.strip()}")
            add_json_entry(
                "flag access attempt",
                f"logged attempt and notified admin, verified flag integrity",
                0.98
            )
            return
    
    # Check for honeypot access
    for path in HONEYPOT_PATHS:
        if path in line:
            log_activity(f"Honeypot triggered: {path} accessed by {ip}")
            add_json_entry(
                "honeypot triggered",
                f"tracked access to {path} from {ip}",
                0.97
            )
            return
    
    # General suspicious activity
    if any(keyword in line.lower() for keyword in ["suspicious", "unusual", "unexpected", "root", "admin"]):
        log_activity(f"Detected suspicious activity from {ip}: {line.strip()}")
        add_json_entry(
            "suspicious activity",
            f"monitoring actions from {ip}",
            0.75
        )

def monitor_red_log():
    """Monitor the red team log for activities."""
    log_activity("Starting red team log monitoring")
    
    # Get the current size of the file
    try:
        file_size = os.path.getsize(RED_LOG)
    except FileNotFoundError:
        file_size = 0
    
    while True:
        try:
            # Check if file exists and has been modified
            if os.path.exists(RED_LOG):
                current_size = os.path.getsize(RED_LOG)
                
                # If file has grown
                if current_size > file_size:
                    with open(RED_LOG, "r") as f:
                        # Seek to the previous position
                        f.seek(file_size)
                        
                        # Read new lines
                        new_lines = f.readlines()
                        
                        # Process each new line
                        for line in new_lines:
                            analyze_log_entry(line)
                    
                    # Update file size
                    file_size = current_size
            
            # Wait before checking again
            time.sleep(1)
            
        except Exception as e:
            log_activity(f"Error monitoring red team log: {str(e)}")
            time.sleep(5)

def create_honeypots():
    """Create honeypot files to detect reconnaissance."""
    log_activity("Creating honeypot files to detect reconnaissance")
    
    for path in HONEYPOT_PATHS:
        try:
            with open(path, "w") as f:
                f.write("# Honeypot file - Access will be logged\n")
                f.write("DB_PASSWORD=S3cr3tP@ssw0rd!\n")
                f.write("API_KEY=honeypot_trigger_8675309\n")
            
            log_activity(f"Created honeypot at {path}")
            add_json_entry(
                "honeypot deployment",
                f"created decoy file at {path}",
                0.95
            )
        except Exception as e:
            log_activity(f"Error creating honeypot {path}: {str(e)}")

def main():
    """Main function."""
    log_activity("Blue Team Monitor starting")
    
    # Initialize logs
    initialize_logs()
    
    # Create honeypot files
    create_honeypots()
    
    # Monitor red team log
    monitor_red_log()

if __name__ == "__main__":
    main()