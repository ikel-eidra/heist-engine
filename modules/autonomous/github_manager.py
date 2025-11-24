#!/usr/bin/env python3
"""
GitHub Manager
==============

Handles all GitHub operations for autonomous code fixing.
Brain uses this to read, modify, and commit its own code.
"""

import os
import base64
import requests
from typing import Dict, List, Optional
from datetime import datetime


class GitHubManager:
    """Manages GitHub repository operations"""
    
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN not found in environment variables")
            
        self.repo_owner = "ikel-eidra"
        self.repo_name = "heist-engine"
        
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        print(f"🔗 GitHub Manager initialized for {self.repo_owner}/{self.repo_name}")
    
    def read_file(self, filepath: str, branch: str = "main") -> Optional[str]:
        """
        Read a file from the repository
        
        Args:
            filepath: Path to file in repo (e.g., "modules/the_brain.py")
            branch: Branch name
            
        Returns:
            File content as string, or None if not found
        """
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/contents/{filepath}"
        params = {"ref": branch}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                content = base64.b64decode(data['content']).decode('utf-8')
                print(f"✅ Read file: {filepath} ({len(content)} characters)")
                return content
            elif response.status_code == 404:
                print(f"❌ File not found: {filepath}")
                return None
            else:
                print(f"❌ Error reading file: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Exception reading file: {e}")
            return None
    
    def get_file_sha(self, filepath: str, branch: str = "main") -> Optional[str]:
        """Get the SHA hash of a file (needed for updates)"""
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/contents/{filepath}"
        params = {"ref": branch}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            if response.status_code == 200:
                return response.json()['sha']
            return None
        except:
            return None
    
    def create_branch(self, new_branch: str, from_branch: str = "main") -> bool:
        """
        Create a new branch
        
        Args:
            new_branch: Name of new branch (e.g., "brain-fix/issue-123")
            from_branch: Source branch
            
        Returns:
            True if successful
        """
        # Get SHA of source branch
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/git/ref/heads/{from_branch}"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            if response.status_code != 200:
                print(f"❌ Could not get source branch SHA")
                return False
            
            source_sha = response.json()['object']['sha']
            
            # Create new branch
            create_url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/git/refs"
            data = {
                "ref": f"refs/heads/{new_branch}",
                "sha": source_sha
            }
            
            response = requests.post(create_url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 201:
                print(f"✅ Created branch: {new_branch}")
                return True
            elif response.status_code == 422:
                print(f"⚠️  Branch already exists: {new_branch}")
                return True  # Branch exists, that's okay
            else:
                print(f"❌ Error creating branch: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Exception creating branch: {e}")
            return False
    
    def commit_file(
        self, 
        filepath: str, 
        content: str, 
        commit_message: str, 
        branch: str = "main"
    ) -> bool:
        """
        Commit a file to the repository
        
        Args:
            filepath: Path to file in repo
            content: New file content
            commit_message: Commit message
            branch: Target branch
            
        Returns:
            True if successful
        """
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/contents/{filepath}"
        
        # Get current file SHA (if file exists)
        current_sha = self.get_file_sha(filepath, branch)
        
        # Encode content
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        data = {
            "message": commit_message,
            "content": encoded_content,
            "branch": branch
        }
        
        if current_sha:
            data["sha"] = current_sha
        
        try:
            response = requests.put(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code in [200, 201]:
                result = response.json()
                commit_sha = result['commit']['sha']
                print(f"✅ Committed: {filepath}")
                print(f"   Commit: {commit_sha[:7]}")
                print(f"   Message: {commit_message}")
                return True
            else:
                print(f"❌ Commit failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Exception committing file: {e}")
            return False
    
    def create_pull_request(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ) -> Optional[str]:
        """
        Create a pull request
        
        Args:
            title: PR title
            body: PR description
            head_branch: Source branch
            base_branch: Target branch
            
        Returns:
            PR URL if successful
        """
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/pulls"
        
        data = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            
            if response.status_code == 201:
                pr_data = response.json()
                pr_url = pr_data['html_url']
                print(f"✅ Pull request created: {pr_url}")
                return pr_url
            else:
                print(f"❌ PR creation failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"❌ Exception creating PR: {e}")
            return None
    
    def auto_merge_branch(self, branch: str, into: str = "main") -> bool:
        """
        Auto-merge a branch (for minor fixes)
        
        Args:
            branch: Source branch
            into: Target branch
            
        Returns:
            True if successful
        """
        # For now, create a PR - in future can implement auto-merge
        pr_url = self.create_pull_request(
            title=f"🤖 Auto-fix from Brain: {branch}",
            body=f"Automated fix applied by Autonomous Brain.\n\nBranch: `{branch}`\nTarget: `{into}`",
            head_branch=branch,
            base_branch=into
        )
        
        return pr_url is not None
    
    def list_files(self, directory: str = "", branch: str = "main") -> List[str]:
        """
        List files in a directory
        
        Args:
            directory: Directory path (empty for root)
            branch: Branch name
            
        Returns:
            List of file paths
        """
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/contents/{directory}"
        params = {"ref": branch}
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                items = response.json()
                files = [item['path'] for item in items if item['type'] == 'file']
                print(f"📁 Found {len(files)} files in {directory or 'root'}")
                return files
            else:
                print(f"❌ Error listing files: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Exception listing files: {e}")
            return []


if __name__ == "__main__":
    # Test the GitHub manager
    print("🧪 Testing GitHub Manager\n")
    
    github = GitHubManager()
    
    # Test: Read a file
    print("\n1. Reading the_brain.py...")
    content = github.read_file("modules/the_brain.py")
    if content:
        print(f"   First 100 chars: {content[:100]}...")
    
    # Test: List files
    print("\n2. Listing files in modules/...")
    files = github.list_files("modules")
    for f in files[:5]:
        print(f"   - {f}")
    
    print("\n✅ GitHub Manager test complete!")
