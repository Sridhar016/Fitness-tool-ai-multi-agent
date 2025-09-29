import os
import json
import requests
from typing import Dict, Any, List
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate

FEEDBACK_FILE = os.path.join("data", "feedback_data.json")

class NutritionAgent:
    def __init__(self):
        # Nutritionix API setup
        self.api_url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
        self.app_id = os.getenv("NUTRITIONIX_APP_ID", "")
        self.api_key = os.getenv("NUTRITIONIX_API_KEY", "")
        # LLM setup (Ollama via LangChain)
        self.llm = Ollama(model="llama3.2")
        # Prompt template
        self.prompt = PromptTemplate.from_template("""
        Create a one-day meal plan with exactly 5 meals in this order:
        1. Breakfast
        2. Morning Snack
        3. Lunch
        4. Afternoon Snack
        5. Dinner
        For a {level} looking to {goal}. {preferences}
        {dietary_restrictions}
        Return just the meal names in order, one per line.
        """)
        os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
        if not os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, "w") as f:
                json.dump([], f)

    def _load_feedback(self) -> List[Dict[str, Any]]:
        """Safely load feedback JSON"""
        try:
            with open(FEEDBACK_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                else:
                    return []
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_feedback(self, feedback_data: List[Dict[str, Any]]):
        """Save feedback back to JSON"""
        with open(FEEDBACK_FILE, "w") as f:
            json.dump(feedback_data, f, indent=4)

    def store_feedback(self, user: str, feedback: str):
        """Add new feedback entry for a user"""
        feedback_data = self._load_feedback()
        feedback_data.append({"user": user, "feedback": feedback})
        self._save_feedback(feedback_data)

    def _fetch_nutrition(self, meal: str) -> Dict[str, Any]:
        """Fetch nutrition data with fallback estimates"""
        # Predefined estimates for specific meals
        estimates = {
            "avocado and egg omelette": {"cal": 731.82, "p": 29.76, "c": 33.04, "f": 55.94},
            "cottage cheese with cucumber": {"cal": 139.79, "p": 13.55, "c": 11.64, "f": 4.93},
            "grilled chicken with brown rice": {"cal": 420.66, "p": 60.76, "c": 28.52, "f": 7.64},
            "carrot sticks with hummus": {"cal": 149.62, "p": 5.87, "c": 20.26, "f": 6.05},
            "baked salmon with asparagus": {"cal": 889.44, "p": 84.99, "c": 23.56, "f": 48.72}
        }
        # Check if the meal matches any predefined estimates
        for key, values in estimates.items():
            if key in meal.lower():
                return {
                    "calories": values["cal"],
                    "protein": values["p"],
                    "carbs": values["c"],
                    "fat": values["f"]
                }
        # If no match, try to fetch from Nutritionix API
        if not self.app_id or not self.api_key:
            return {"calories": 300, "protein": 20, "carbs": 30, "fat": 10}
        headers = {
            "x-app-id": self.app_id,
            "x-app-key": self.api_key,
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json={"query": meal}
            )
            response.raise_for_status()
            data = response.json()
            if "foods" in data and data["foods"]:
                item = data["foods"][0]
                return {
                    "calories": item.get("nf_calories", 300),
                    "protein": item.get("nf_protein", 20),
                    "carbs": item.get("nf_total_carbohydrate", 30),
                    "fat": item.get("nf_total_fat", 10)
                }
            else:
                return {"calories": 300, "protein": 20, "carbs": 30, "fat": 10}
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch nutrition data: {e}")
            return {"calories": 300, "protein": 20, "carbs": 30, "fat": 10}

    def generate_meal_plan(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate categorized meal plan"""
        # Prepare prompt
        goal = user_profile.get("goal", "maintain health")
        level = user_profile.get("level", "beginner")
        preferences = user_profile.get("meal_preference", "")
        dietary_restrictions = ""
        # Get dietary preferences from feedback
        dietary_prefs = user_profile.get("dietary_preferences", {})
        if dietary_prefs.get("protein_source") == "fish":
            dietary_restrictions = "All meals must include fish as the primary protein source."
        elif dietary_prefs.get("diet_type") == "vegetarian":
            dietary_restrictions = "All meals must be vegetarian (no meat, fish, or poultry)."

        # Apply past feedback
        feedback_data = self._load_feedback()
        user_name = user_profile.get("name")
        user_feedback = [f["feedback"] for f in feedback_data if f["user"] == user_name]
        if user_feedback:
            preferences += " Past feedback: " + "; ".join(user_feedback)

        # Generate meals using LLM
        formatted_prompt = self.prompt.format(
            goal=goal, level=level, preferences=preferences,
            dietary_restrictions=dietary_restrictions
        )
        response = self.llm.invoke(formatted_prompt)
        meal_descriptions = [m.strip() for m in response.split('\n') if m.strip()][:5]
        # Categorize meals
        meal_types = ["Breakfast", "Morning Snack", "Lunch", "Afternoon Snack", "Dinner"]
        meal_plan = []
        for i, (meal_type, meal) in enumerate(zip(meal_types, meal_descriptions)):
            nutrition = self._fetch_nutrition(meal)
            meal_plan.append({
                "type": meal_type,
                "description": meal,
                "calories": nutrition["calories"],
                "protein": nutrition["protein"],
                "carbs": nutrition["carbs"],
                "fat": nutrition["fat"]
            })
        return {"meal_plan": meal_plan}

# Example usage with a different user name
if __name__ == "__main__":
    agent = NutritionAgent()
    # Add some feedback for a different user
    agent.store_feedback("john_doe", "Prefer vegetarian meals")
    agent.store_feedback("john_doe", "Need higher protein options")
    user_profile = {
        "name": "john_doe",
        "goal": "lose fat",
        "level": "beginner",
        "preferences": "prefers spicy food",
        "dietary_preferences": {"diet_type": "vegetarian"}
    }
    result = agent.generate_meal_plan(user_profile)
    print("Your Meal Plan:")
    for meal in result["meal_plan"]:
        print(f"{meal['type']}: {meal['description']} → "
              f"{meal['calories']} kcal | P: {meal['protein']}g | "
              f"C: {meal['carbs']}g | F: {meal['fat']}g")
