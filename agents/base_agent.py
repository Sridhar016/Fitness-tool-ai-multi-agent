import json
import os
from datetime import datetime

class BaseAgent:
    """
    Base class for all agent classes providing common functionality
    such as logging capabilities.
    """
    def __init__(self):
        """Initialize the BaseAgent with log file setup."""
        self.log_file = 'data/agent_logs.json'
        # Create the data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        # Initialize the log file
        self._initialize_log_file()

    def _initialize_log_file(self):
        """Initialize the log file if it doesn't exist."""
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                json.dump([], f)  # Initialize with an empty list

    def log_decision(self, user_id: str, action: str, reason: str = None, metadata: dict = None) -> None:
        """
        Log agent decisions with full context.

        This method records all agent decisions along with the reasoning and
        any relevant metadata to provide a complete audit trail.

        Args:
            user_id: ID of the user affected by the action
            action: Description of the action taken
            reason: Why the action was taken (optional)
            metadata: Additional context data (optional) containing any relevant information
                     about the decision or system state

        Returns:
            None
        """
        # Create the log entry with basic information
        log_entry = {
            'timestamp': datetime.now().isoformat(),  # Current timestamp in ISO format
            'agent': self.__class__.__name__,         # Name of the agent class
            'action': action,                        # Description of the action
            'user_id': user_id                       # User associated with the action
        }

        # Add optional fields if provided
        if reason:
            log_entry['reason'] = reason  # Add reason for the action
        if metadata:
            log_entry['metadata'] = metadata  # Add additional context data

        # Read existing logs from file
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
                # Ensure logs is a list (in case file is corrupted)
                if not isinstance(logs, list):
                    logs = []
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or contains invalid JSON, start with empty list
            logs = []

        # Append the new log entry
        logs.append(log_entry)

        # Write the updated logs back to file
        try:
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)  # Write with pretty-print formatting
        except Exception as e:
            print(f"Failed to log action: {e}")  # Print error if logging fails

    def _log_action(self, user_id: str, message: str) -> None:
        """
        Legacy method for backward compatibility with existing code.

        This method exists to maintain compatibility with older code that
        expects the _log_action method signature.

        Args:
            user_id: ID of the user
            message: Log message

        Returns:
            None
        """
        # Convert the old-style log call to the new format
        self.log_decision(user_id, message)
