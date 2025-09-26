import os
import requests
import json
from typing import Dict, Any, List
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate

class NutritionAgent:
    def __init__(self):
        self.llm = Ollama(model="llama3.2")
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

    def _fetch_nutrition(self, meal: str) -> Dict[str, Any]:
        """Get nutrition data with fallback estimates"""
        # In a real implementation, this would call the Nutritionix API
        # For this example, we'll use estimated values
        estimates = {
            "avocado and egg omelette": {"cal": 731.82, "p": 29.76, "c": 33.04, "f": 55.94},
            "cottage cheese with cucumber": {"cal": 139.79, "p": 13.55, "c": 11.64, "f": 4.93},
            "grilled chicken with brown rice": {"cal": 420.66, "p": 60.76, "c": 28.52, "f": 7.64},
            "carrot sticks with hummus": {"cal": 149.62, "p": 5.87, "c": 20.26, "f": 6.05},
            "baked salmon with asparagus": {"cal": 889.44, "p": 84.99, "c": 23.56, "f": 48.72}
        }

        for key, values in estimates.items():
            if key in meal.lower():
                return {
                    "calories": values["cal"],
                    "protein": values["p"],
                    "carbs": values["c"],
                    "fat": values["f"]
                }

        # Default values
        return {"calories": 300, "protein": 20, "carbs": 30, "fat": 10}

    def generate_meal_plan(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate categorized meal plan"""
        # Prepare prompt
        goal = user_profile.get("goal", "maintain health")
        level = user_profile.get("level", "beginner")
        preferences = user_profile.get("preferences", "")
        dietary_restrictions = ""

        # Get dietary preferences from feedback
        dietary_prefs = user_profile.get("dietary_preferences", {})
        if dietary_prefs.get("protein_source") == "fish":
            dietary_restrictions = "All meals must include fish as the primary protein source."
        elif dietary_prefs.get("diet_type") == "vegetarian":
            dietary_restrictions = "All meals must be vegetarian (no meat, fish, or poultry)."

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

# Example usage:
user_profile = {
    "goal": "lose fat",
    "level": "beginner",
    "preferences": "prefers high-protein meals",
    "dietary_preferences": {"protein_source": "fish"}
}

agent = NutritionAgent()
result = agent.generate_meal_plan(user_profile)

# Display results
print("Your Meal Plan:")
for meal in result["meal_plan"]:
    print(f"{meal['type']}: {meal['description']} → "
          f"{meal['calories']} kcal | Protein: {meal['protein']}g | "
          f"Carbs: {meal['carbs']}g | Fat: {meal['fat']}g")
    