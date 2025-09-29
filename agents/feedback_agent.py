import json
import os
from datetime import datetime
from typing import Dict, Any, List
from agents.base_agent import BaseAgent

DATA_FILE = os.path.join("data", "feedback_data.json")

class FeedbackAgent(BaseAgent):
    def __init__(self):
        """Initialize the feedback agent with data storage"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w") as f:
                json.dump({}, f)

    def process_feedback(self, user_name: str, feedback_text: str) -> Dict[str, Any]:
        """
        Process user feedback and suggest appropriate adjustments

        Args:
            user_name: Name of the user providing feedback
            feedback_text: The feedback text from the user

        Returns:
            Dictionary containing feedback processing results and suggested actions
        """
        try:
            # Load existing feedback data
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
        except:
            data = {}

        # Store the feedback with timestamp
        feedback_entry = {
            "feedback": feedback_text,
            "timestamp": datetime.now().isoformat(),
            "processed": False
        }
        data.setdefault(user_name, []).append(feedback_entry)

        # Save updated feedback data
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

        # Analyze feedback and determine action
        feedback_lower = feedback_text.lower()
        result = {
            "stored": True,
            "feedback_text": feedback_text,
            "timestamp": feedback_entry["timestamp"],
            "suggested_action": None,
            "adjustments_needed": False,
            "nutrition_adjustment": False,
            "workout_adjustment": False,
            "updated_profile": {},
            "meal_preferences": None
        }

        # Workout-related feedback
        if "workout" in feedback_lower:
            if any(word in feedback_lower for word in ["hard", "intense", "difficult", "tough"]):
                result["suggested_action"] = "decrease_intensity"
                result["adjustments_needed"] = True
                result["workout_adjustment"] = True
                result["updated_profile"]["workout_intensity"] = "lower"
            elif any(word in feedback_lower for word in ["easy", "simple", "light"]):
                result["suggested_action"] = "increase_intensity"
                result["adjustments_needed"] = True
                result["workout_adjustment"] = True
                result["updated_profile"]["workout_intensity"] = "higher"

        # Nutrition-related feedback
        elif any(word in feedback_lower for word in ["meal", "food", "diet", "eat", "fish", "chicken", "vegetarian", "vegan"]):
            result["nutrition_adjustment"] = True
            result["adjustments_needed"] = True

            # Specific food preferences
            if "fish" in feedback_lower and ("only" in feedback_lower or "just" in feedback_lower):
                result["suggested_action"] = "fish_only_meals"
                result["meal_preferences"] = {"protein_source": "fish", "exclusive": True}
                result["updated_profile"]["dietary_preferences"] = {
                    "protein_source": "fish",
                    "restrictions": ["no_chicken", "no_mutton", "no_vegetarian"]
                }
            elif "chicken" in feedback_lower and ("only" in feedback_lower or "just" in feedback_lower):
                result["suggested_action"] = "chicken_only_meals"
                result["meal_preferences"] = {"protein_source": "chicken", "exclusive": True}
                result["updated_profile"]["dietary_preferences"] = {
                    "protein_source": "chicken",
                    "restrictions": ["no_fish", "no_mutton", "no_vegetarian"]
                }
            elif "vegetarian" in feedback_lower:
                result["suggested_action"] = "vegetarian_meals"
                result["meal_preferences"] = {"diet_type": "vegetarian"}
                result["updated_profile"]["dietary_preferences"] = {
                    "diet_type": "vegetarian",
                    "restrictions": ["no_meat", "no_fish", "no_chicken"]
                }
            elif "vegan" in feedback_lower:
                result["suggested_action"] = "vegan_meals"
                result["meal_preferences"] = {"diet_type": "vegan"}
                result["updated_profile"]["dietary_preferences"] = {
                    "diet_type": "vegan",
                    "restrictions": ["no_meat", "no_fish", "no_chicken", "no_dairy", "no_eggs"]
                }
            elif any(word in feedback_lower for word in ["not tasty", "bad taste", "don't like", "disgusting"]):
                result["suggested_action"] = "change_meal"
                result["meal_preferences"] = {"issue": "taste", "action": "replace"}
                result["updated_profile"]["meal_preferences"] = "adjusted"
            elif any(word in feedback_lower for word in ["too much", "too large", "big portion"]):
                result["suggested_action"] = "reduce_portion"
                result["meal_preferences"] = {"issue": "portion", "action": "reduce"}
                result["updated_profile"]["portion_size"] = "smaller"

        # General feedback
        else:
            if any(word in feedback_lower for word in ["good", "great", "like", "enjoy"]):
                result["suggested_action"] = "positive_feedback"
            else:
                result["suggested_action"] = "recorded"

        # Mark feedback as processed
        feedback_entry["processed"] = True
        feedback_entry["action_taken"] = result["suggested_action"]

        # Save the updated feedback with processing status
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

        return result

    def get_feedback_history(self, user_name: str) -> List[Dict[str, Any]]:
        """Get feedback history for a specific user"""
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
            return data.get(user_name, [])
        except:
            return []

    def get_recent_feedback(self, user_name: str, count: int = 5) -> List[Dict[str, Any]]:
        """Get most recent feedback entries for a user"""
        feedback = self.get_feedback_history(user_name)
        return sorted(feedback, key=lambda x: x["timestamp"], reverse=True)[:count]

    def get_common_issues(self, user_name: str) -> Dict[str, int]:
        """Analyze common feedback issues for a user"""
        feedback = self.get_feedback_history(user_name)
        issues = {
            "workout_too_hard": 0,
            "workout_too_easy": 0,
            "meal_not_tasty": 0,
            "portion_too_large": 0,
            "positive": 0,
            "dietary_preferences": 0
        }

        for entry in feedback:
            text = entry["feedback"].lower()
            if any(word in text for word in ["hard", "intense", "difficult", "tough"]):
                issues["workout_too_hard"] += 1
            elif any(word in text for word in ["easy", "simple", "light"]):
                issues["workout_too_easy"] += 1
            elif any(word in text for word in ["not tasty", "bad taste", "don't like", "disgusting"]):
                issues["meal_not_tasty"] += 1
            elif any(word in text for word in ["too much", "too large", "big portion"]):
                issues["portion_too_large"] += 1
            elif any(word in text for word in ["fish", "chicken", "vegetarian", "vegan"]):
                issues["dietary_preferences"] += 1
            elif any(word in text for word in ["good", "great", "like", "enjoy"]):
                issues["positive"] += 1

        return issues
