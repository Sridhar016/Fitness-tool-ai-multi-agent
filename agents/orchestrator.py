from agents.profile_agent import ProfileAgent
from agents.workout_agent import WorkoutAgent
from agents.nutrition_agent import NutritionAgent
from agents.progress_agent import ProgressAgent
from agents.feedback_agent import FeedbackAgent
from agents.coordinator_agent import CoordinatorAgent
from agents.dynamic_rule_generator import DynamicRuleGenerator
from datetime import datetime
from typing import Dict, Any
import json

class Orchestrator:
    def __init__(self):
        self.profile_agent = ProfileAgent()
        self.workout_agent = WorkoutAgent()
        self.nutrition_agent = NutritionAgent()
        self.progress_agent = ProgressAgent()
        self.feedback_agent = FeedbackAgent()
        self.coordinator_agent = CoordinatorAgent()
        self.dynamic_rule_generator = DynamicRuleGenerator()

    def run(self, user_profile: Dict[str, Any], feedback_text: str = None) -> Dict[str, Any]:
        user_id = user_profile.get("name", "Unknown")
        result = {
            "profile": user_profile,
            "workout_text": "",
            "nutrition_text": "",
            "nutrition_json": None,
            "progress": [],
            "progress_text": "",
            "feedback_result": None,
            "conflict_resolution": None,
            "dynamic_rules": None
        }

        # Update user profile
        self.profile_agent.update_profile({user_profile["name"]: user_profile})

        # --- Generate initial workout and nutrition plans ---
        workout_text = self.workout_agent.generate_plan(user_profile)
        result["workout_text"] = workout_text
        nutrition_result = self.nutrition_agent.generate_meal_plan(user_profile)
        result["nutrition_json"] = nutrition_result
        result["nutrition_text"] = nutrition_result.get("plan_text", "")

        # --- Process feedback if provided ---
        if feedback_text:
            feedback_result = self.feedback_agent.process_feedback(
                user_profile["name"], feedback_text
            )
            result["feedback_result"] = feedback_result

            # Update profile with feedback preferences
            updated_profile = {**user_profile, **feedback_result.get("updated_profile", {})}
            self.profile_agent.update_profile({user_profile["name"]: updated_profile})

            # --- Resolve conflicts using Coordinator Agent ---
            conflict_resolution = self.coordinator_agent.resolve_conflicts(updated_profile, feedback_result)
            result["conflict_resolution"] = conflict_resolution

            # --- Generate dynamic rules if conflicts exist ---
            dynamic_rules = None
            if conflict_resolution.get("conflicts"):
                dynamic_rules = self.dynamic_rule_generator.generate_rules(updated_profile, feedback_result)
                result["dynamic_rules"] = dynamic_rules

            # --- Adjust workout plan based on conflict resolution and dynamic rules ---
            if conflict_resolution.get("resolutions") or dynamic_rules is not None:
                workout_text = self.workout_agent.generate_plan(
                    user_profile=updated_profile,
                    conflict_resolutions=conflict_resolution.get("resolutions", []),
                    dynamic_rules=dynamic_rules
                )
                result["workout_text"] = workout_text

            # --- Adjust nutrition plan based on feedback ---
            if feedback_result.get("nutrition_adjustment", False):
                nutrition_result = self.nutrition_agent.generate_meal_plan(updated_profile)
                result["nutrition_json"] = nutrition_result
                result["nutrition_text"] = nutrition_result.get("plan_text", "")

        # --- Load progress data ---
        result["progress"] = self.progress_agent.load_progress(user_profile["name"])
        result["progress_text"] = "\n".join([
            f"Day {p.get('day', '-')} | {p.get('timestamp', '-')} | "
            f"Weight: {p.get('weight', '-')}kg | "
            f"Duration: {p.get('duration_min', '-')}min | "
            f"Calories: {p.get('calories_burned', '-')}"
            for p in result["progress"]
        ])

        return result

