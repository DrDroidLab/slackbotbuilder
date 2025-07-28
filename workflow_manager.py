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
    
    def match_workflow(self, message_data: Dict[str, Any], channel_name: str, user_name: str, is_app_mentioned: bool = False) -> Optional[Dict]:
        """
        Match a message against defined workflows
        
        Args:
            message_data: The Slack message data
            channel_name: Name of the channel
            user_name: Name of the user
            is_app_mentioned: Whether the app is mentioned in the message
            
        Returns:
            Dict: Matching workflow or None if no match
        """
        message_text = message_data.get('text', '')
        
        for workflow in self.workflows:
            # Check if app mention is required
            app_mention_required = workflow.get('app_mention_required', False)
            if app_mention_required and not is_app_mentioned:
                continue
            
            # Check channel name (optional - skip if not specified)
            if 'channel_name' in workflow:
                workflow_channel = workflow.get('channel_name', '*')
                if workflow_channel != '*' and workflow_channel.lower() != channel_name.lower():
                    continue
            
            # Check user name (optional - skip if not specified)
            if 'user_name' in workflow:
                workflow_user = workflow.get('user_name', '*')
                if workflow_user != '*' and workflow_user.lower() != user_name.lower():
                    continue
            
            # Check wildcard pattern (optional - skip if not specified)
            if 'wildcard' in workflow:
                wildcard_pattern = workflow.get('wildcard', '')
                if wildcard_pattern:
                    # Convert wildcard pattern to regex for matching
                    # * matches any sequence of characters
                    # ? matches any single character
                    regex_pattern = wildcard_pattern.replace('*', '.*').replace('?', '.')
                    
                    # Add word boundaries for exact word matching (unless wildcard contains *)
                    if '*' not in wildcard_pattern:
                        regex_pattern = r'\b' + regex_pattern + r'\b'
                    
                    try:
                        if not re.search(regex_pattern, message_text, re.IGNORECASE):
                            continue
                    except re.error as e:
                        logger.error(f"Invalid wildcard pattern '{wildcard_pattern}': {e}")
                        continue
            
            logger.info(f"Workflow matched: {workflow.get('name', 'unnamed')}")
            return workflow
        
        return None
    
    def execute_workflow(self, workflow: Dict, message_data: Dict[str, Any]) -> Optional[Dict]:
        """
        Execute a workflow action script or prompt
        
        Args:
            workflow: The workflow configuration
            message_data: The Slack message data
            
        Returns:
            Dict: Response from the script or None if failed
        """
        # Check for action_prompt first
        action_prompt = workflow.get('action_prompt')
        if action_prompt:
            return self.execute_prompt_workflow(workflow, message_data)
        
        # Fall back to action_script
        action_script = workflow.get('action_script')
        if action_script:
            return self.execute_script_workflow(workflow, message_data)
        
        logger.error("No action_script or action_prompt specified in workflow")
        return None
    
    def execute_script_workflow(self, workflow: Dict, message_data: Dict[str, Any]) -> Optional[Dict]:
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
    
    def execute_prompt_workflow(self, workflow: Dict, message_data: Dict[str, Any]) -> Optional[Dict]:
        """
        Execute a workflow action prompt
        
        Args:
            workflow: The workflow configuration
            message_data: The Slack message data
            
        Returns:
            Dict: Response from the prompt executor or None if failed
        """
        try:
            action_prompt = workflow.get('action_prompt')
            if not action_prompt:
                logger.error("No action prompt specified in workflow")
                return None
            
            # Read the prompt file
            prompt_path = os.path.join('prompts', action_prompt)
            if not os.path.exists(prompt_path):
                logger.error(f"Action prompt file not found: {prompt_path}")
                return None
            
            # Read the prompt content
            with open(prompt_path, 'r') as file:
                prompt_content = file.read()
            
            # Execute the prompt executor script
            script_path = os.path.join('scripts', 'prompt_executor.py')
            if not os.path.exists(script_path):
                logger.error(f"Prompt executor script not found: {script_path}")
                return None
            
            # Make script executable
            os.chmod(script_path, 0o755)
            
            # Prepare the message JSON with prompt content
            enhanced_message = message_data.copy()
            enhanced_message['prompt_content'] = prompt_content
            
            message_json = json.dumps(enhanced_message)
            
            # Execute the script
            logger.info(f"Executing prompt workflow: {action_prompt}")
            result = subprocess.run(
                [sys.executable, script_path, message_json],
                capture_output=True,
                text=True,
                timeout=60  # 60 second timeout for LLM operations
            )
            
            if result.returncode != 0:
                logger.error(f"Prompt execution failed: {result.stderr}")
                return None
            
            # Parse the response
            try:
                response = json.loads(result.stdout.strip())
                logger.info(f"Prompt response: {response}")
                return response
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON response from prompt executor: {e}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Prompt execution timed out: {action_prompt}")
            return None
        except Exception as e:
            logger.error(f"Error executing prompt workflow: {e}")
            return None
    
    def process_message(self, message_data: Dict[str, Any], channel_name: str, user_name: str, is_app_mentioned: bool = False) -> Optional[Dict]:
        """
        Process a message through the workflow system
        
        Args:
            message_data: The Slack message data
            channel_name: Name of the channel
            user_name: Name of the user
            is_app_mentioned: Whether the app is mentioned in the message
            
        Returns:
            Dict: Response to send back to Slack or None if no workflow matched
        """
        # Match workflow
        workflow = self.match_workflow(message_data, channel_name, user_name, is_app_mentioned)
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
        return {
            "total_workflows": len(self.workflows),
            "workflows_file": self.workflows_file
        }

# Global instance
workflow_manager = WorkflowManager() 