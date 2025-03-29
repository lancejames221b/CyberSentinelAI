# Blue Team Defense System for CTF Simulation

This repository contains a comprehensive Blue Team defense system for a Capture The Flag (CTF) simulation. The system is designed to detect and respond to Red Team activities, protect the flag, and log all defensive actions. 

**For a comprehensive overview of the entire Autonomous AI CTF Battle System, see [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md).**

## System Components

1. **blue_defense.sh**: The main defense script that monitors for intrusion attempts, implements adaptive defenses, and logs activities.
2. **blue_monitor.py**: A Python script that provides more sophisticated monitoring capabilities, including pattern detection and analysis.
3. **blue_targeted_defense.py**: A targeted defense script that specifically counters the Red Team's attack vectors.
4. **start_ctf.sh**: The master control script that starts the CTF competition and coordinates the agents.

## Features

### Monitoring Capabilities
- SSH login attempt detection
- Port scanning detection
- File system exploration monitoring
- Exploitation attempt detection
- Flag access monitoring

### Defensive Measures
- Honeypot deployment in common reconnaissance paths
- IP blocking for brute force attempts
- Service patching for known exploits
- File access restrictions
- Data loss prevention for flag exfiltration

### Logging and Reporting
- Real-time activity logging to `blue_team.log`
- Structured assessment output to `blue_agent_output.json`
- Confidence scoring for detections
- Timestamp recording for all activities

## How to Use

1. Ensure the Docker container is running:
   ```
   docker ps | grep ghostops_ctf
   ```

2. Start the CTF competition:
   ```
   ./start_ctf.sh
   ```

3. Monitor the logs in real-time:
   ```
   tail -f logs/blue_team.log
   ```

4. View the structured output:
   ```
   cat logs/blue_agent_output.json
   ```

## Alternative: Isolated Environment

For a more isolated environment where Red and Blue teams operate independently:

1. Set up the isolated environments:
   ```
   ./agent_controller.sh
   ```

2. Start the competition in isolated mode:
   ```
   ./ctf-arena/master_control.sh
   ```

3. View Blue team activity:
   ```
   tmux attach -t blue_agent
   ```

4. View Red team activity:
   ```
   tmux attach -t red_agent
   ```

## Defense Strategy

Our defense strategy follows a multi-layered approach:

1. **Reconnaissance Detection**: Identify when the Red Team is scanning or exploring the system.
2. **Access Control**: Monitor and restrict SSH access and authentication attempts.
3. **System Hardening**: Implement file permissions and access controls to protect sensitive data.
4. **Deception**: Deploy honeypots to detect and mislead attackers.
5. **Monitoring**: Continuously monitor logs, processes, and network connections for suspicious activities.
6. **Response**: Implement adaptive defenses based on detected threats.
7. **Logging**: Maintain comprehensive logs of all activities and responses.

## Flag Protection

The flag is located at `/var/ctf/flag.txt` and is protected by:
- Restricted file permissions (400)
- Directory permissions (711)
- Continuous monitoring for access attempts
- Alerts for any flag exfiltration attempts

## Conclusion

This Blue Team defense system provides a robust and adaptive defense against Red Team attacks in the CTF simulation. It demonstrates effective security monitoring, threat detection, and incident response capabilities.