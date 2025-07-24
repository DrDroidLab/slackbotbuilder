import yaml
import os
import re
import subprocess
import json
import logging
from typing import Dict, List, Optional, Any
import sys

logger = logging.getLogger(__name__)

class WorkflowManager:
    def __init__(self, workflows_file: str = "workflows.yaml"):
        """
        Initialize the workflow manager
        
        Args:
            workflows_file: Path to the workflows YAML file
        """
        self.workflows_file = workflows_file
        self.workflows = []
        self.load_workflows()
    
    def load_workflows(self) -> bool:
        """
        Load workflows from the YAML file
        
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(self.workflows_file):
                logger.warning(f"Workflows file not found: {self.workflows_file}")
                return False
            
            with open(self.workflows_file, 'r') as file:
                data = yaml.safe_load(file)
            
            self.workflows = data.get('workflows', [])
            logger.info(f"Loaded {len(self.workflows)} workflows from {self.workflows_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading workflows: {e}")
            return False
    
    def reload_workflows(self) -> bool:
        """
        Reload workflows from the file
        
        Returns:
            bool: True if reloaded successfully, False otherwise
        """
        return self.load_workflows()
    
    def match_workflow(self, message_data: Dict[str, Any], channel_name: str, user_name: str) -> Optional[Dict]:
        """
        Match a message against defined workflows
        
        Args:
            message_data: The Slack message data
            channel_name: Name of the channel
            user_name: Name of the user
            
        Returns:
            Dict: Matching workflow or None if no match
        """
        message_text = message_data.get('text', '')
        
        for workflow in self.workflows:
            if not workflow.get('enabled', True):
                continue
            
            # Check channel name
            workflow_channel = workflow.get('channel_name', '*')
            if workflow_channel != '*' and workflow_channel.lower() != channel_name.lower():
                continue
            
            # Check user name
            workflow_user = workflow.get('user_name', '*')
            if workflow_user != '*' and workflow_user.lower() != user_name.lower():
                continue
            
            # Check regex pattern
            regex_pattern = workflow.get('regex', '')
            if regex_pattern and not re.search(regex_pattern, message_text, re.IGNORECASE):
                continue
            
            logger.info(f"Workflow matched: {workflow.get('name', 'unnamed')}")
            return workflow
        
        return None
    
    def execute_workflow(self, workflow: Dict, message_data: Dict[str, Any]) -> Optional[Dict]:
        """
        Execute a workflow action script
        
        Args:
            workflow: The workflow configuration
            message_data: The Slack message data
            
        Returns:
            Dict: Response from the script or None if failed
        """
        try:
            action_script = workflow.get('action_script')
            if not action_script:
                logger.error("No action script specified in workflow")
                return None
            
            # Construct the script path
            script_path = os.path.join('scripts', action_script)
            if not os.path.exists(script_path):
                logger.error(f"Action script not found: {script_path}")
                return None
            
            # Make script executable
            os.chmod(script_path, 0o755)
            
            # Prepare the message JSON
            message_json = json.dumps(message_data)
            
            # Execute the script
            logger.info(f"Executing workflow script: {script_path}")
            result = subprocess.run(
                [sys.executable, script_path, message_json],
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Script execution failed: {result.stderr}")
                return None
            
            # Parse the response
            try:
                response = json.loads(result.stdout.strip())
                logger.info(f"Script response: {response}")
                return response
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response from script: {e}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Script execution timed out: {action_script}")
            return None
        except Exception as e:
            logger.error(f"Error executing workflow: {e}")
            return None
    
    def process_message(self, message_data: Dict[str, Any], channel_name: str, user_name: str) -> Optional[Dict]:
        """
        Process a message through the workflow system
        
        Args:
            message_data: The Slack message data
            channel_name: Name of the channel
            user_name: Name of the user
            
        Returns:
            Dict: Response to send back to Slack or None if no workflow matched
        """
        # Match workflow
        workflow = self.match_workflow(message_data, channel_name, user_name)
        print('workflow', workflow)
        if not workflow:
            return None
        
        # Execute workflow
        return self.execute_workflow(workflow, message_data)
    
    def get_workflows_summary(self) -> Dict:
        """
        Get a summary of loaded workflows
        
        Returns:
            Dict: Summary of workflows
        """
        enabled_count = sum(1 for w in self.workflows if w.get('enabled', True))
        disabled_count = len(self.workflows) - enabled_count
        
        return {
            "total_workflows": len(self.workflows),
            "enabled_workflows": enabled_count,
            "disabled_workflows": disabled_count,
            "workflows_file": self.workflows_file
        }

# Global instance
workflow_manager = WorkflowManager() 