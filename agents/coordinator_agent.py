import json
import os
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from agents.dynamic_rule_generator import DynamicRuleGenerator

class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.profile_file = os.path.join("data", "user_profiles.json")
        self.feedback_file = os.path.join("data", "feedback_data.json")
        self.rule_generator = DynamicRuleGenerator()

    def _initialize_data_files(self) -> None:
        """Initialize all required data files."""
        # Initialize user profiles if not exists
        if not os.path.exists(self.profile_file):
            with open(self.profile_file, 'w') as f:
                json.dump({}, f)
        # Initialize user feedback if not exists
        if not os.path.exists(self.feedback_file):
            with open(self.feedback_file, 'w') as f:
                json.dump({}, f)

    def load_profile_data(self) -> Dict[str, Any]:
        """Load profile data from the profile file."""
        with open(self.profile_file, 'r') as f:
            return json.load(f)

    def load_feedback_data(self) -> Dict[str, Any]:
        """Load feedback data from the feedback file."""
        with open(self.feedback_file, 'r') as f:
            return json.load(f)

    def resolve_conflicts(self, profile_data: Optional[Dict[str, Any]] = None, feedback_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Resolve conflicts between profile constraints and feedback suggestions.
        If profile_data or feedback_data is not provided, load it from the respective files.
        """
        if profile_data is None:
            profile_data = self.load_profile_data()
        if feedback_data is None:
            feedback_data = self.load_feedback_data()

        # Ensure profile_data and feedback_data are not None
        profile_data = profile_data or {}
        feedback_data = feedback_data or {}
        user_id = profile_data.get("name", "Unknown")

        # Log initial conflict check
        self.log_decision(
            user_id=user_id,
            action="Checking for conflicts",
            metadata={
                "profile": profile_data,
                "feedback": feedback_data
            }
        )

        # Generate dynamic rules based on the current context
        dynamic_rules = self.rule_generator.generate_rules(profile_data, feedback_data)
        conflicts = []
        resolutions = []

        # Check for intensity conflicts with injuries
        suggested_action = feedback_data.get("feedback", "").lower()
        preferences = profile_data.get("health_info", "").lower()
        if "high intensity" in suggested_action and "injury" in preferences:
            conflicts.append("Increase intensity conflicts with injury status")
            resolutions.append({
                "adjustment": "Decrease intensity and suggest low-impact exercises",
                "safe_fallback": "Swap high-impact exercises with cycling or swimming",
                "priority": "high"
            })


        # Check for health conditions vs. exercise intensity
        health_conditions = profile_data.get("health_info", "").lower()
        if "high intensity" in suggested_action and ("heart_condition" in health_conditions or "asthma" in health_conditions):
            conflicts.append("High-intensity workout conflicts with health condition")
            resolutions.append({
                "adjustment": "Suggest low-intensity exercises",
                "safe_fallback": "Replace running with walking or yoga",
                "priority": "high"
            })

        # Check for weather conditions vs. outdoor activities
        weather_condition = feedback_data.get("feedback", "").lower()
        workout_type = feedback_data.get("feedback", "").lower()
        if "outdoor" in workout_type and ("rain" in weather_condition or "extreme_heat" in weather_condition):
            conflicts.append("Outdoor workout conflicts with weather conditions")
            resolutions.append({
                "adjustment": "Suggest indoor workouts",
                "safe_fallback": "Replace outdoor running with treadmill or indoor cycling",
                "priority": "medium"
            })



        # Log conflicts and resolutions
        self.log_decision(
            user_id=user_id,
            action="Conflicts resolved",
            metadata={
                "conflicts": conflicts,
                "resolutions": resolutions,
                "dynamic_rules": dynamic_rules
            }
        )

        return {
            "conflicts": conflicts,
            "resolutions": resolutions,
            "dynamic_rules": dynamic_rules,
            "status": "resolved" if resolutions else "none"
        }
