# agents/profile_agent.py
import json
import os
from typing import Dict, Any
from datetime import datetime, timedelta
from agents.base_agent import BaseAgent

DATA_FILE = os.path.join("data", "user_profiles.json")

class ProfileAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        os.makedirs("data", exist_ok=True)
        self._initialize_profile_file()

    def _initialize_profile_file(self):
        """Initialize the profile file if it doesn't exist."""
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'w') as f:
                json.dump({}, f)
            self.log_decision("system", "Initialized user profiles file")

    def save_user_profile(self, user_data: Dict[str, Any]) -> None:
        """Save the entire user profiles dictionary to the file."""
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(user_data, f, indent=4)
            self.log_decision("system", "Saved all user profiles")
        except Exception as e:
            self.log_decision("system", f"Failed to save profiles: {str(e)}")
            raise

    def load_user_profile(self) -> Dict[str, Any]:
        """Load all user profiles from the file."""
        try:
            with open(DATA_FILE, 'r') as f:
                profiles = json.load(f)
                # Ensure we return a dictionary
                if not isinstance(profiles, dict):
                    self.log_decision("system", "Profile file corrupted, returning empty dict")
                    return {}
            self.log_decision("system", "Loaded user profiles")
            return profiles
        except (FileNotFoundError, json.JSONDecodeError):
            self.log_decision("system", "No profiles found, returning empty dict")
            return {}

    def update_profile(self, new_profile: Dict[str, Any]) -> str:
        """Update or add a new profile to the existing profiles."""
        profiles = self.load_user_profile()

        # Validate input
        if not isinstance(new_profile, dict):
            self.log_decision("system", "Invalid profile data received")
            raise ValueError("Profile data must be a dictionary")

        for user_id, profile_data in new_profile.items():
            self.log_decision(
                user_id=user_id,
                action="Updating profile",
                metadata={"updated_fields": list(profile_data.keys())}
            )

        profiles.update(new_profile)
        self.save_user_profile(profiles)
        return "Profile updated successfully."

    def load_all_profiles(self) -> list:
        """Return all usernames for selection."""
        profiles = self.load_user_profile()
        user_ids = list(profiles.keys())
        self.log_decision("system", f"Loaded {len(user_ids)} user profiles")
        return user_ids

    def get_user_plan_status(self, user_id: str) -> Dict[str, Any]:
        """Get a user's current plan status."""
        profiles = self.load_user_profile()
        user_data = profiles.get(user_id, {})

        # Safely check plan expiration
        plan_expired = False
        if user_data.get('plan_end_date'):
            try:
                plan_expired = datetime.fromisoformat(user_data['plan_end_date']) < datetime.now()
            except (TypeError, ValueError):
                pass

        self.log_decision(
            user_id=user_id,
            action="Retrieved plan status",
            metadata={
                "has_plan": bool(user_data.get('plan_start_date')),
                "plan_expired": plan_expired
            }
        )

        return {
            'workout_plan': user_data.get('workout_plan', {}),
            'nutrition_plan': user_data.get('nutrition_plan', {}),
            'plan_start_date': user_data.get('plan_start_date'),
            'plan_end_date': user_data.get('plan_end_date'),
            'progress': user_data.get('progress', [])
        }

    def update_plan_status(self, user_id: str, plan_data: Dict[str, Any]) -> None:
        """Update a user's plan status with new plan data."""
        if not isinstance(plan_data, dict):
            self.log_decision(
                user_id=user_id,
                action="Update plan failed",
                reason="Invalid plan data"
            )
            raise ValueError("Plan data must be a dictionary")

        self.log_decision(
            user_id=user_id,
            action="Updating plan status",
            metadata={"new_plan": bool(plan_data)}
        )

        profiles = self.load_user_profile()
        if user_id not in profiles:
            profiles[user_id] = {}

        # Safely update plan data
        try:
            profiles[user_id].update({
                'workout_plan': plan_data.get('workout_plan', {}),
                'nutrition_plan': plan_data.get('nutrition_plan', {}),
                'plan_start_date': datetime.now().isoformat(),
                'plan_end_date': (datetime.now() + timedelta(days=7)).isoformat(),
                'last_updated': datetime.now().isoformat()
            })

            with open(DATA_FILE, 'w') as f:
                json.dump(profiles, f, indent=4)

            self.log_decision(
                user_id=user_id,
                action="Plan status updated",
                metadata={
                    "plan_duration": "7_days",
                    "plan_types": list(plan_data.keys())
                }
            )
        except Exception as e:
            self.log_decision(
                user_id=user_id,
                action="Failed to update plan status",
                metadata={"error": str(e)}
            )
            raise

    def check_plan_expiration(self, user_id: str) -> bool:
        """Check if user's current plan has expired."""
        status = self.get_user_plan_status(user_id)
        if not status.get('plan_end_date'):
            self.log_decision(user_id, "No active plan found")
            return True

        try:
            is_expired = datetime.fromisoformat(status['plan_end_date']) < datetime.now()
            self.log_decision(
                user_id=user_id,
                action="Checked plan expiration",
                metadata={"is_expired": is_expired}
            )
            return is_expired
        except (TypeError, ValueError):
            self.log_decision(
                user_id=user_id,
                action="Failed to check plan expiration",
                reason="Invalid date format"
            )
            return True
