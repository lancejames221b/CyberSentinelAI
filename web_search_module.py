#!/usr/bin/env python3

"""
Web Search Module for Autonomous CTF Agent Battle
Provides search capabilities to both red and blue team agents
"""

import os
import json
import argparse
import requests
import time
from datetime import datetime

# Configuration and API keys (load from environment variables for security)
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")

# Fallback if environment variables are not set
if not PERPLEXITY_API_KEY or not BRAVE_API_KEY:
    try:
        with open('/root/keys.json', 'r') as f:
            keys_data = json.load(f)
            
            # Find Perplexity API key
            for section in keys_data:
                if "Application Paths" in section:
                    for item in section["Application Paths"]:
                        if "PERPLEXITY_API_KEY" in item:
                            PERPLEXITY_API_KEY = item["PERPLEXITY_API_KEY"]
                if "AI Models" in section:
                    for item in section["AI Models"]:
                        if "PERPLEXITY_API_KEY" in item:
                            PERPLEXITY_API_KEY = item["PERPLEXITY_API_KEY"]
                        
            # Find Brave API key
            for section in keys_data:
                if "Application Paths" in section:
                    for item in section["Application Paths"]:
                        if "BRAVE_SEARCH_API_KEY" in item:
                            BRAVE_API_KEY = item["BRAVE_SEARCH_API_KEY"]
    except Exception as e:
        print(f"Error loading API keys from file: {e}")

# Ensure we have API keys
if not PERPLEXITY_API_KEY:
    raise ValueError("PERPLEXITY_API_KEY not found. Please set environment variable or add to keys.json")
if not BRAVE_API_KEY:
    raise ValueError("BRAVE_API_KEY not found. Please set environment variable or add to keys.json")

class WebSearchModule:
    def __init__(self, log_dir="./logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize log files
        self.search_log_file = os.path.join(log_dir, "web_searches.json")
        
        # Create or load search history
        if os.path.exists(self.search_log_file):
            with open(self.search_log_file, 'r') as f:
                try:
                    self.search_history = json.load(f)
                except json.JSONDecodeError:
                    self.search_history = {"searches": []}
        else:
            self.search_history = {"searches": []}
            with open(self.search_log_file, 'w') as f:
                json.dump(self.search_history, f)
    
    def search_perplexity(self, query, agent_type):
        """Search using Perplexity AI API"""
        url = "https://api.perplexity.ai/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Use pplx-70b-online for most up-to-date results
        payload = {
            "model": "pplx-70b-online",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful AI assistant that provides accurate and up-to-date information for a CTF competition."
                },
                {
                    "role": "user", 
                    "content": query
                }
            ]
        }
        
        search_record = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_type,
            "engine": "perplexity",
            "query": query,
            "results": None,
            "error": None
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"]
            search_record["results"] = content
            
            # Log the search
            self._log_search(search_record)
            
            return {
                "success": True,
                "engine": "perplexity",
                "query": query,
                "results": content
            }
            
        except Exception as e:
            error_message = str(e)
            search_record["error"] = error_message
            self._log_search(search_record)
            
            return {
                "success": False,
                "engine": "perplexity",
                "query": query,
                "error": error_message
            }
    
    def search_brave(self, query, agent_type):
        """Search using Brave Search API"""
        url = "https://api.search.brave.com/res/v1/web/search"
        
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": BRAVE_API_KEY
        }
        
        params = {
            "q": query,
            "count": 10,  # Number of results
            "search_lang": "en"
        }
        
        search_record = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_type,
            "engine": "brave",
            "query": query,
            "results": None,
            "error": None
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            results = response.json()
            
            # Extract relevant information
            web_results = []
            if "web" in results and "results" in results["web"]:
                for result in results["web"]["results"]:
                    web_results.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "description": result.get("description", "")
                    })
            
            search_record["results"] = web_results
            self._log_search(search_record)
            
            return {
                "success": True,
                "engine": "brave",
                "query": query,
                "results": web_results
            }
            
        except Exception as e:
            error_message = str(e)
            search_record["error"] = error_message
            self._log_search(search_record)
            
            return {
                "success": False,
                "engine": "brave",
                "query": query,
                "error": error_message
            }
    
    def search(self, query, engine="perplexity", agent_type="unknown"):
        """Unified search method that can use different engines"""
        if engine.lower() == "perplexity":
            return self.search_perplexity(query, agent_type)
        elif engine.lower() == "brave":
            return self.search_brave(query, agent_type)
        else:
            return {
                "success": False,
                "error": f"Unknown search engine: {engine}"
            }
    
    def _log_search(self, search_record):
        """Log a search to the history file"""
        self.search_history["searches"].append(search_record)
        
        with open(self.search_log_file, 'w') as f:
            json.dump(self.search_history, f, indent=2)
    
    def get_recent_searches(self, agent_type=None, limit=10):
        """Get recent searches, optionally filtered by agent type"""
        searches = self.search_history["searches"]
        
        if agent_type:
            searches = [s for s in searches if s["agent"] == agent_type]
        
        # Sort by timestamp (most recent first) and limit
        searches.sort(key=lambda x: x["timestamp"], reverse=True)
        return searches[:limit]

def main():
    """CLI interface for web search module"""
    parser = argparse.ArgumentParser(description="Web Search Module for CTF Agent Battle")
    parser.add_argument("--log-dir", type=str, default="./logs", help="Directory for log files")
    parser.add_argument("--query", type=str, help="Search query")
    parser.add_argument("--engine", type=str, choices=["perplexity", "brave"], default="perplexity", help="Search engine to use")
    parser.add_argument("--agent", type=str, choices=["red", "blue"], required=True, help="Agent type (red or blue)")
    parser.add_argument("--recent", action="store_true", help="Get recent searches instead of performing a new search")
    parser.add_argument("--limit", type=int, default=10, help="Limit for recent searches")
    
    args = parser.parse_args()
    
    search_module = WebSearchModule(log_dir=args.log_dir)
    
    if args.recent:
        recent_searches = search_module.get_recent_searches(agent_type=args.agent, limit=args.limit)
        print(json.dumps(recent_searches, indent=2))
    else:
        if not args.query:
            parser.error("--query is required for search")
        
        result = search_module.search(args.query, engine=args.engine, agent_type=args.agent)
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 