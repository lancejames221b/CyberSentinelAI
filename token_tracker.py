#!/usr/bin/env python3

"""
Token Tracker for Autonomous CTF Agent Battle
Monitors token usage and calculates costs for both red and blue teams
"""

import json
import time
import os
import threading
import argparse
from datetime import datetime

# Cost configuration
CLAUDE_SONNET_INPUT_COST = 10  # $10 per 1M input tokens
CLAUDE_SONNET_OUTPUT_COST = 30  # $30 per 1M output tokens
BUDGET_PER_AGENT = 100  # $100 per agent

class TokenTracker:
    def __init__(self, log_dir="./logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize tracking data
        self.agent_data = {
            "red": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost": 0,
                "turns": 0,
                "start_time": None,
                "last_updated": None,
                "actions": []
            },
            "blue": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost": 0,
                "turns": 0,
                "start_time": None,
                "last_updated": None,
                "actions": []
            }
        }
        
        # Initialize log files
        self.log_files = {
            "red": os.path.join(log_dir, "red_token_usage.json"),
            "blue": os.path.join(log_dir, "blue_token_usage.json"),
            "summary": os.path.join(log_dir, "cost_summary.json")
        }
        
        # Create or reset log files
        for file_path in self.log_files.values():
            with open(file_path, 'w') as f:
                json.dump({}, f)
        
        # Auto-save timer
        self.save_interval = 60  # Save every 60 seconds
        self.save_thread = None
        self.running = False
    
    def start_tracking(self, agent_type):
        """Start tracking for an agent (red or blue)"""
        if agent_type not in ["red", "blue"]:
            raise ValueError("Agent type must be 'red' or 'blue'")
        
        if not self.agent_data[agent_type]["start_time"]:
            self.agent_data[agent_type]["start_time"] = datetime.now().isoformat()
            self.agent_data[agent_type]["last_updated"] = datetime.now().isoformat()
            self._save_agent_data(agent_type)
            print(f"Started tracking {agent_type} agent at {self.agent_data[agent_type]['start_time']}")
    
    def record_usage(self, agent_type, input_tokens, output_tokens, action_description):
        """Record token usage for an agent"""
        if agent_type not in ["red", "blue"]:
            raise ValueError("Agent type must be 'red' or 'blue'")
        
        # Calculate costs
        input_cost = (input_tokens / 1_000_000) * CLAUDE_SONNET_INPUT_COST
        output_cost = (output_tokens / 1_000_000) * CLAUDE_SONNET_OUTPUT_COST
        total_action_cost = input_cost + output_cost
        
        # Update agent data
        self.agent_data[agent_type]["input_tokens"] += input_tokens
        self.agent_data[agent_type]["output_tokens"] += output_tokens
        self.agent_data[agent_type]["total_cost"] += total_action_cost
        self.agent_data[agent_type]["turns"] += 1
        self.agent_data[agent_type]["last_updated"] = datetime.now().isoformat()
        
        # Record the action
        action_data = {
            "timestamp": datetime.now().isoformat(),
            "action": action_description,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "action_cost": total_action_cost,
            "running_total_cost": self.agent_data[agent_type]["total_cost"]
        }
        self.agent_data[agent_type]["actions"].append(action_data)
        
        # Save the updated data
        self._save_agent_data(agent_type)
        
        # Check budget
        remaining_budget = BUDGET_PER_AGENT - self.agent_data[agent_type]["total_cost"]
        
        print(f"[{agent_type.upper()}] Recorded {input_tokens} input tokens, {output_tokens} output tokens")
        print(f"[{agent_type.upper()}] Action cost: ${total_action_cost:.2f}, Total cost: ${self.agent_data[agent_type]['total_cost']:.2f}")
        print(f"[{agent_type.upper()}] Remaining budget: ${remaining_budget:.2f}")
        
        return {
            "action_cost": total_action_cost,
            "total_cost": self.agent_data[agent_type]["total_cost"],
            "remaining_budget": remaining_budget,
            "budget_exceeded": remaining_budget <= 0
        }
    
    def get_usage_summary(self, agent_type=None):
        """Get usage summary for a specific agent or both"""
        if agent_type and agent_type not in ["red", "blue"]:
            raise ValueError("Agent type must be 'red' or 'blue'")
        
        if agent_type:
            return self._get_agent_summary(agent_type)
        else:
            # Return summary for both agents
            summary = {
                "red": self._get_agent_summary("red"),
                "blue": self._get_agent_summary("blue"),
                "battle_duration": self._get_battle_duration(),
                "timestamp": datetime.now().isoformat()
            }
            
            # Save summary
            with open(self.log_files["summary"], 'w') as f:
                json.dump(summary, f, indent=2)
            
            return summary
    
    def _get_agent_summary(self, agent_type):
        """Get detailed summary for a specific agent"""
        data = self.agent_data[agent_type]
        remaining_budget = BUDGET_PER_AGENT - data["total_cost"]
        
        return {
            "input_tokens": data["input_tokens"],
            "output_tokens": data["output_tokens"],
            "total_tokens": data["input_tokens"] + data["output_tokens"],
            "total_cost": data["total_cost"],
            "remaining_budget": remaining_budget,
            "budget_percentage_used": (data["total_cost"] / BUDGET_PER_AGENT) * 100,
            "turns_taken": data["turns"],
            "start_time": data["start_time"],
            "last_updated": data["last_updated"],
            "budget_exceeded": remaining_budget <= 0
        }
    
    def _get_battle_duration(self):
        """Calculate the total battle duration"""
        red_start = datetime.fromisoformat(self.agent_data["red"]["start_time"]) if self.agent_data["red"]["start_time"] else datetime.now()
        blue_start = datetime.fromisoformat(self.agent_data["blue"]["start_time"]) if self.agent_data["blue"]["start_time"] else datetime.now()
        
        earliest_start = min(red_start, blue_start)
        seconds = (datetime.now() - earliest_start).total_seconds()
        
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return {
            "hours": int(hours),
            "minutes": int(minutes),
            "seconds": int(seconds),
            "total_seconds": seconds
        }
    
    def _save_agent_data(self, agent_type):
        """Save agent data to the corresponding log file"""
        with open(self.log_files[agent_type], 'w') as f:
            json.dump(self.agent_data[agent_type], f, indent=2)
    
    def start_auto_save(self):
        """Start auto-save thread"""
        self.running = True
        self.save_thread = threading.Thread(target=self._auto_save_routine)
        self.save_thread.daemon = True
        self.save_thread.start()
    
    def stop_auto_save(self):
        """Stop auto-save thread"""
        self.running = False
        if self.save_thread:
            self.save_thread.join(timeout=1)
    
    def _auto_save_routine(self):
        """Auto-save routine that runs in background thread"""
        while self.running:
            self.get_usage_summary()  # This saves all current data
            time.sleep(self.save_interval)
    
    def is_budget_exceeded(self, agent_type):
        """Check if an agent has exceeded their budget"""
        if agent_type not in ["red", "blue"]:
            raise ValueError("Agent type must be 'red' or 'blue'")
        
        remaining_budget = BUDGET_PER_AGENT - self.agent_data[agent_type]["total_cost"]
        return remaining_budget <= 0

def main():
    """CLI interface for token tracker"""
    parser = argparse.ArgumentParser(description="Token Tracker for CTF Agent Battle")
    parser.add_argument("--log-dir", type=str, default="./logs", help="Directory for log files")
    parser.add_argument("--action", type=str, choices=["start", "record", "summary"], required=True, help="Action to perform")
    parser.add_argument("--agent", type=str, choices=["red", "blue"], help="Agent type (red or blue)")
    parser.add_argument("--input-tokens", type=int, help="Number of input tokens used")
    parser.add_argument("--output-tokens", type=int, help="Number of output tokens used")
    parser.add_argument("--description", type=str, help="Description of the action")
    
    args = parser.parse_args()
    
    tracker = TokenTracker(log_dir=args.log_dir)
    
    if args.action == "start":
        if not args.agent:
            parser.error("--agent is required for start action")
        tracker.start_tracking(args.agent)
    
    elif args.action == "record":
        if not args.agent:
            parser.error("--agent is required for record action")
        if args.input_tokens is None or args.output_tokens is None:
            parser.error("--input-tokens and --output-tokens are required for record action")
        if not args.description:
            parser.error("--description is required for record action")
        
        result = tracker.record_usage(
            args.agent, 
            args.input_tokens, 
            args.output_tokens, 
            args.description
        )
        
        print(json.dumps(result, indent=2))
    
    elif args.action == "summary":
        summary = tracker.get_usage_summary(args.agent)
        print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    main() 