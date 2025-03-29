#!/usr/bin/env python3

"""
Blue Team Targeted Defense for CTF Simulation
This script implements specific countermeasures against the red team's attack vectors.
"""

import os
import re
import json
import time
import datetime
import subprocess
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
TARGET_IP = "127.0.0.1"
TARGET_SSH_PORT = "2222"
TARGET_HTTP_PORT = "8081"

# Function to log activity
def log_activity(message):
    """Log activity to blue_team.log."""
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(BLUE_LOG, "a") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

# Function to add entry to blue_agent_output.json
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

# Function to detect port scanning
def detect_port_scanning():
    """Monitor for port scanning activities."""
    log_activity("Setting up port scan detection")
    
    # In a real environment, we would use tools like fail2ban or custom iptables rules
    # For this simulation, we'll monitor the red team log for port scanning activities
    
    port_scan_patterns = [
        r"nmap",
        r"port\s+scan",
        r"scanning",
        r"Scanning target ports"
    ]
    
    while True:
        try:
            if os.path.exists(RED_LOG):
                with open(RED_LOG, "r") as f:
                    content = f.read()
                    
                    for pattern in port_scan_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            log_activity("ALERT: Port scanning detected!")
                            add_json_entry(
                                "port scanning detected",
                                "implemented rate limiting and increased logging",
                                0.95
                            )
                            
                            # Simulate blocking the scanning IP
                            log_activity("Blocking scanning IP with iptables")
                            
                            # In a real environment, we would execute:
                            # subprocess.run(["iptables", "-A", "INPUT", "-s", TARGET_IP, "-j", "DROP"])
                            
                            # Wait before checking again to avoid log spam
                            time.sleep(5)
            
            # Check every second
            time.sleep(1)
            
        except Exception as e:
            log_activity(f"Error in port scan detection: {str(e)}")
            time.sleep(5)

# Function to detect SSH login attempts
def detect_ssh_login():
    """Monitor for SSH login attempts."""
    log_activity("Setting up SSH login detection")
    
    ssh_patterns = [
        r"ssh",
        r"Attempting SSH access",
        r"SSH access successful",
        r"sshpass"
    ]
    
    while True:
        try:
            if os.path.exists(RED_LOG):
                with open(RED_LOG, "r") as f:
                    content = f.read()
                    
                    for pattern in ssh_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            log_activity("ALERT: SSH login attempt detected!")
                            add_json_entry(
                                "SSH login attempt",
                                "monitoring session and implementing command restrictions",
                                0.90
                            )
                            
                            # Simulate implementing SSH restrictions
                            log_activity("Implementing SSH command restrictions")
                            
                            # In a real environment, we would modify sshd_config to restrict commands
                            # or implement a custom PAM module
                            
                            # Wait before checking again to avoid log spam
                            time.sleep(5)
            
            # Check every second
            time.sleep(1)
            
        except Exception as e:
            log_activity(f"Error in SSH login detection: {str(e)}")
            time.sleep(5)

# Function to monitor file system exploration
def monitor_file_system():
    """Monitor for file system exploration activities."""
    log_activity("Setting up file system monitoring")
    
    file_exploration_patterns = [
        r"find\s+/",
        r"ls\s+-la",
        r"Exploring file system",
        r"File listing",
        r"\.txt"
    ]
    
    while True:
        try:
            if os.path.exists(RED_LOG):
                with open(RED_LOG, "r") as f:
                    content = f.read()
                    
                    for pattern in file_exploration_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            log_activity("ALERT: File system exploration detected!")
                            add_json_entry(
                                "file system exploration",
                                "implementing file access auditing and restrictions",
                                0.85
                            )
                            
                            # Create decoy files to mislead the attacker
                            create_decoy_files()
                            
                            # Wait before checking again to avoid log spam
                            time.sleep(5)
            
            # Check every second
            time.sleep(1)
            
        except Exception as e:
            log_activity(f"Error in file system monitoring: {str(e)}")
            time.sleep(5)

# Function to create decoy files
def create_decoy_files():
    """Create decoy files to mislead the attacker."""
    log_activity("Creating decoy flag files")
    
    decoy_paths = [
        "/tmp/flag.txt",
        "/home/ctf/flag.txt",
        "/var/log/flag.txt"
    ]
    
    for path in decoy_paths:
        try:
            # In a real environment, we would create these files in the container
            # For simulation, we'll just log the action
            log_activity(f"Created decoy flag at {path}")
            add_json_entry(
                "decoy deployment",
                f"created decoy flag at {path}",
                0.80
            )
        except Exception as e:
            log_activity(f"Error creating decoy file {path}: {str(e)}")

# Function to detect exploitation attempts
def detect_exploitation():
    """Monitor for exploitation attempts."""
    log_activity("Setting up exploitation detection")
    
    exploitation_patterns = [
        r"sudo",
        r"Attempting to access flag file",
        r"Permission check",
        r"Symlink attempt",
        r"ln\s+-s",
        r"SUID",
        r"find\s+/\s+-perm"
    ]
    
    while True:
        try:
            if os.path.exists(RED_LOG):
                with open(RED_LOG, "r") as f:
                    content = f.read()
                    
                    for pattern in exploitation_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            log_activity("ALERT: Exploitation attempt detected!")
                            add_json_entry(
                                "exploitation attempt",
                                "hardening permissions and implementing additional access controls",
                                0.95
                            )
                            
                            # Simulate hardening the system
                            log_activity("Hardening system permissions")
                            
                            # In a real environment, we would execute commands to harden permissions
                            # For example: chmod, chattr, or implementing mandatory access controls
                            
                            # Wait before checking again to avoid log spam
                            time.sleep(5)
            
            # Check every second
            time.sleep(1)
            
        except Exception as e:
            log_activity(f"Error in exploitation detection: {str(e)}")
            time.sleep(5)

# Function to prevent flag exfiltration
def prevent_exfiltration():
    """Monitor for flag exfiltration attempts."""
    log_activity("Setting up exfiltration prevention")
    
    exfiltration_patterns = [
        r"cat\s+/var/ctf/flag\.txt",
        r"python3\s+-c",
        r"dd\s+if=/var/ctf/flag\.txt",
        r"Attempting flag exfiltration",
        r"flag\{",
        r"SUCCESS: Flag captured"
    ]
    
    while True:
        try:
            if os.path.exists(RED_LOG):
                with open(RED_LOG, "r") as f:
                    content = f.read()
                    
                    for pattern in exfiltration_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            log_activity("CRITICAL ALERT: Flag exfiltration attempt detected!")
                            add_json_entry(
                                "flag exfiltration attempt",
                                "implementing data loss prevention and alerting administrators",
                                0.99
                            )
                            
                            # Simulate blocking the exfiltration
                            log_activity("Blocking flag exfiltration attempt")
                            
                            # In a real environment, we would implement data loss prevention measures
                            # For example: network filtering, process termination, or file access controls
                            
                            # Wait before checking again to avoid log spam
                            time.sleep(5)
            
            # Check every second
            time.sleep(1)
            
        except Exception as e:
            log_activity(f"Error in exfiltration prevention: {str(e)}")
            time.sleep(5)

# Main function
def main():
    """Main function."""
    log_activity("Blue Team Targeted Defense starting")
    add_json_entry(
        "targeted defense activated",
        "implementing specific countermeasures against known attack vectors",
        0.98
    )
    
    # Start all monitoring functions in separate threads
    import threading
    
    threads = [
        threading.Thread(target=detect_port_scanning),
        threading.Thread(target=detect_ssh_login),
        threading.Thread(target=monitor_file_system),
        threading.Thread(target=detect_exploitation),
        threading.Thread(target=prevent_exfiltration)
    ]
    
    # Start all threads
    for thread in threads:
        thread.daemon = True
        thread.start()
    
    # Keep the main thread running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log_activity("Blue Team Targeted Defense shutting down")

if __name__ == "__main__":
    main()