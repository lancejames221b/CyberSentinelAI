#!/usr/bin/env python3

"""
Tool Installer Module for Autonomous CTF Agent Battle
Allows agents to safely install and use tools in their isolated environments
"""

import os
import json
import argparse
import subprocess
import shutil
import tempfile
import hashlib
import re
import requests
from datetime import datetime

class ToolInstaller:
    def __init__(self, agent_type, workspace_dir=None, log_dir="./logs"):
        if agent_type not in ["red", "blue"]:
            raise ValueError("Agent type must be 'red' or 'blue'")
        
        self.agent_type = agent_type
        self.log_dir = log_dir
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Set up workspace directory
        if workspace_dir is None:
            workspace_dir = f"./workspace_{agent_type}"
        self.workspace_dir = os.path.abspath(workspace_dir)
        os.makedirs(self.workspace_dir, exist_ok=True)
        
        # Set up tool directory
        self.tools_dir = os.path.join(self.workspace_dir, "tools")
        os.makedirs(self.tools_dir, exist_ok=True)
        
        # Initialize log file
        self.log_file = os.path.join(log_dir, f"{agent_type}_tool_installer.json")
        
        # Load or create tool installation history
        if os.path.exists(self.log_file):
            with open(self.log_file, 'r') as f:
                try:
                    self.history = json.load(f)
                except json.JSONDecodeError:
                    self.history = {"installations": []}
        else:
            self.history = {"installations": []}
            with open(self.log_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        
        # Define allowed package managers and repositories
        self.allowed_package_managers = {
            "apt": {
                "command": "apt-get",
                "install_cmd": ["apt-get", "install", "-y"],
                "update_cmd": ["apt-get", "update"],
                "allowed_for": ["red", "blue"]
            },
            "pip": {
                "command": "pip3",
                "install_cmd": ["pip3", "install"],
                "allowed_for": ["red", "blue"]
            },
            "go": {
                "command": "go",
                "install_cmd": ["go", "install"],
                "allowed_for": ["red", "blue"]
            },
            "npm": {
                "command": "npm",
                "install_cmd": ["npm", "install", "-g"],
                "allowed_for": ["red", "blue"]
            },
            "git": {
                "command": "git",
                "install_cmd": ["git", "clone"],
                "allowed_for": ["red", "blue"]
            }
        }
        
        # Define blocked packages for security reasons
        self.blocked_packages = {
            "apt": [
                "john", "hydra", "wireshark", "nmap", "netcat", "telnet"
            ],
            "pip": [
                "requests", "paramiko", "cryptography", "pycrypto"
            ],
            "go": [],
            "npm": [],
            "git": [
                "https://github.com/vanhauser-thc/thc-hydra",
                "https://github.com/openwall/john",
                "https://github.com/nmap/nmap",
                "https://github.com/sullo/nikto"
            ]
        }
        
        # For red team, unblock offensive tools
        if agent_type == "red":
            self.blocked_packages["apt"] = []
            self.blocked_packages["pip"] = []
            self.blocked_packages["git"] = []
    
    def _log_installation(self, package_manager, package_name, success, error=None, output=None):
        """Log package installation attempt"""
        installation_record = {
            "timestamp": datetime.now().isoformat(),
            "agent": self.agent_type,
            "package_manager": package_manager,
            "package": package_name,
            "success": success,
            "error": error,
            "output": output
        }
        
        self.history["installations"].append(installation_record)
        
        with open(self.log_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def _check_package_allowed(self, package_manager, package_name):
        """Check if the package is allowed to be installed"""
        # Check if package manager is allowed for this agent
        if package_manager not in self.allowed_package_managers:
            return False, f"Package manager '{package_manager}' not allowed"
        
        if self.agent_type not in self.allowed_package_managers[package_manager]["allowed_for"]:
            return False, f"Package manager '{package_manager}' not allowed for {self.agent_type} agent"
        
        # Check if package is in blocked list
        if package_name in self.blocked_packages.get(package_manager, []):
            return False, f"Package '{package_name}' is blocked for security reasons"
        
        # Additional security checks for git repositories
        if package_manager == "git" and package_name.startswith("http"):
            # Check if any part of the URL contains blocked terms
            for blocked in self.blocked_packages.get("git", []):
                if blocked in package_name:
                    return False, f"Git repository '{package_name}' is blocked for security reasons"
        
        return True, None
    
    def _sanitize_package_name(self, package_name):
        """Sanitize package name to prevent command injection"""
        # Remove any shell special characters
        return re.sub(r'[;&|<>$`\\"\']', '', package_name)
    
    def install_package(self, package_manager, package_name):
        """Install a package using the specified package manager"""
        # Sanitize inputs
        package_manager = package_manager.lower()
        package_name = self._sanitize_package_name(package_name)
        
        # Check if package is allowed
        allowed, reason = self._check_package_allowed(package_manager, package_name)
        if not allowed:
            self._log_installation(package_manager, package_name, False, error=reason)
            return {
                "success": False,
                "error": reason
            }
        
        # Check if package manager is available
        if not shutil.which(self.allowed_package_managers[package_manager]["command"]):
            error_msg = f"Package manager '{package_manager}' is not installed"
            self._log_installation(package_manager, package_name, False, error=error_msg)
            return {
                "success": False,
                "error": error_msg
            }
        
        # Construct the installation command
        install_cmd = list(self.allowed_package_managers[package_manager]["install_cmd"])
        install_cmd.append(package_name)
        
        # For apt, update package lists first
        if package_manager == "apt":
            try:
                update_cmd = self.allowed_package_managers[package_manager]["update_cmd"]
                subprocess.run(update_cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to update package lists: {e.stderr}"
                self._log_installation(package_manager, package_name, False, error=error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
        
        # Execute the installation command
        try:
            result = subprocess.run(install_cmd, check=True, capture_output=True, text=True)
            self._log_installation(package_manager, package_name, True, output=result.stdout)
            return {
                "success": True,
                "package_manager": package_manager,
                "package": package_name,
                "output": result.stdout
            }
        except subprocess.CalledProcessError as e:
            error_msg = f"Installation failed: {e.stderr}"
            self._log_installation(package_manager, package_name, False, error=error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def download_tool(self, url, filename=None):
        """Download a tool from a URL to the tools directory"""
        # Determine filename if not provided
        if filename is None:
            filename = url.split("/")[-1]
        
        # Sanitize filename
        filename = self._sanitize_package_name(filename)
        
        # Create full path
        filepath = os.path.join(self.tools_dir, filename)
        
        try:
            # Download the file
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Save to file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Make it executable
            os.chmod(filepath, 0o755)
            
            # Calculate file hash for verification
            sha256_hash = hashlib.sha256()
            with open(filepath, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            
            # Log the download
            self._log_installation("download", url, True, output=filepath)
            
            return {
                "success": True,
                "url": url,
                "filepath": filepath,
                "sha256": sha256_hash.hexdigest()
            }
            
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            self._log_installation("download", url, False, error=error_msg)
            return {
                "success": False,
                "error": error_msg
            }
    
    def compile_tool(self, source_code, language, filename):
        """Compile tool from source code"""
        # Sanitize filename
        filename = self._sanitize_package_name(filename)
        
        # Create full path
        filepath = os.path.join(self.tools_dir, filename)
        
        # Create a temporary directory for compilation
        with tempfile.TemporaryDirectory() as tmpdir:
            source_path = os.path.join(tmpdir, f"source.{language}")
            
            # Write the source code to a file
            with open(source_path, 'w') as f:
                f.write(source_code)
            
            try:
                # Compile based on language
                if language == "c":
                    result = subprocess.run(
                        ["gcc", source_path, "-o", filepath],
                        check=True, capture_output=True, text=True
                    )
                elif language == "cpp":
                    result = subprocess.run(
                        ["g++", source_path, "-o", filepath],
                        check=True, capture_output=True, text=True
                    )
                elif language == "go":
                    result = subprocess.run(
                        ["go", "build", "-o", filepath, source_path],
                        check=True, capture_output=True, text=True
                    )
                else:
                    return {
                        "success": False,
                        "error": f"Unsupported language: {language}"
                    }
                
                # Make executable
                os.chmod(filepath, 0o755)
                
                # Log the compilation
                self._log_installation("compile", filename, True, output=result.stdout)
                
                return {
                    "success": True,
                    "language": language,
                    "filepath": filepath
                }
                
            except subprocess.CalledProcessError as e:
                error_msg = f"Compilation failed: {e.stderr}"
                self._log_installation("compile", filename, False, error=error_msg)
                return {
                    "success": False,
                    "error": error_msg
                }
    
    def get_installed_tools(self):
        """Get a list of all installed tools"""
        apt_packages = []
        pip_packages = []
        tools = []
        
        # List apt packages
        try:
            result = subprocess.run(["dpkg", "-l"], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if line.startswith("ii "):
                        parts = line.split()
                        if len(parts) >= 2:
                            apt_packages.append(parts[1])
        except:
            pass
        
        # List pip packages
        try:
            result = subprocess.run(["pip3", "list"], capture_output=True, text=True)
            if result.returncode == 0:
                for line in result.stdout.splitlines()[2:]:  # Skip header
                    parts = line.split()
                    if len(parts) >= 1:
                        pip_packages.append(parts[0])
        except:
            pass
        
        # List custom tools
        if os.path.exists(self.tools_dir):
            tools = os.listdir(self.tools_dir)
        
        return {
            "apt_packages": apt_packages,
            "pip_packages": pip_packages,
            "custom_tools": tools,
            "tools_dir": self.tools_dir
        }

def main():
    """CLI interface for tool installer"""
    parser = argparse.ArgumentParser(description="Tool Installer for CTF Agent Battle")
    parser.add_argument("--agent", type=str, choices=["red", "blue"], required=True, help="Agent type (red or blue)")
    parser.add_argument("--log-dir", type=str, default="./logs", help="Directory for log files")
    parser.add_argument("--workspace-dir", type=str, help="Workspace directory for the agent")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Install package command
    install_parser = subparsers.add_parser("install", help="Install a package")
    install_parser.add_argument("--package-manager", type=str, required=True, choices=["apt", "pip", "go", "npm", "git"], help="Package manager to use")
    install_parser.add_argument("--package", type=str, required=True, help="Package name or repository URL")
    
    # Download tool command
    download_parser = subparsers.add_parser("download", help="Download a tool")
    download_parser.add_argument("--url", type=str, required=True, help="URL to download from")
    download_parser.add_argument("--filename", type=str, help="Filename to save as")
    
    # Compile tool command
    compile_parser = subparsers.add_parser("compile", help="Compile a tool from source code")
    compile_parser.add_argument("--language", type=str, required=True, choices=["c", "cpp", "go"], help="Programming language")
    compile_parser.add_argument("--source", type=str, required=True, help="Source code (quoted)")
    compile_parser.add_argument("--filename", type=str, required=True, help="Output filename")
    
    # List tools command
    subparsers.add_parser("list", help="List installed tools")
    
    args = parser.parse_args()
    
    installer = ToolInstaller(args.agent, workspace_dir=args.workspace_dir, log_dir=args.log_dir)
    
    if args.command == "install":
        result = installer.install_package(args.package_manager, args.package)
        print(json.dumps(result, indent=2))
    
    elif args.command == "download":
        result = installer.download_tool(args.url, args.filename)
        print(json.dumps(result, indent=2))
    
    elif args.command == "compile":
        result = installer.compile_tool(args.source, args.language, args.filename)
        print(json.dumps(result, indent=2))
    
    elif args.command == "list":
        result = installer.get_installed_tools()
        print(json.dumps(result, indent=2))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 