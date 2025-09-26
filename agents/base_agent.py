# agents/base_agent.py
import json
import os
from datetime import datetime

class BaseAgent:
    def __init__(self):
        self.log_file = 'data/agent_logs.json'
        os.makedirs('data', exist_ok=True)
        self._initialize_log_file()

    def _initialize_log_file(self):
        """Initialize the log file if it doesn't exist."""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                json.dump([], f)

    def log_decision(self, user_id: str, action: str, reason: str = None, metadata: dict = None) -> None:
        """
        Log agent decisions with full context.
        Args:
            user_id: ID of the user
            action: Description of the action taken
            reason: Why the action was taken (optional)
            metadata: Additional context data (optional)
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'agent': self.__class__.__name__,
            'action': action,
            'user_id': user_id
        }

        if reason:
            log_entry['reason'] = reason
        if metadata:
            log_entry['metadata'] = metadata

        # Read existing logs
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
                # Ensure logs is a list
                if not isinstance(logs, list):
                    logs = []
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []

        # Append new log entry
        logs.append(log_entry)

        # Write back to file
        try:
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
        except Exception as e:
            print(f"Failed to log action: {e}")

    def _log_action(self, user_id: str, message: str) -> None:
        """Legacy method for backward compatibility."""
        self.log_decision(user_id, message)
