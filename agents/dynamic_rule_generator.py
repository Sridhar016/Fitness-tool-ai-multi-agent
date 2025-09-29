import json
import os
import csv
from typing import Dict, Any, List
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate

class DynamicRuleGenerator:
    def __init__(self):
        self.llm = Ollama(model="llama3.2")
        self.prompt = PromptTemplate.from_template("""
        Based on the following user data and context, generate appropriate fallback rules:
        User Profile: {user_profile}
        Workout Data: {workout_data}
        Nutrition Data: {nutrition_data}
        Progress Data: {progress_data}
        Feedback Data: {feedback_data}
        Generate rules to resolve any conflicts and ensure the plan is adaptable to the user's needs.
        Don't Generate any Pseudo Code
        The output should be in Short summary.                                           
        """)

    def generate_rules(self, user_profile: Dict[str, Any], feedback_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate dynamic rules based on user profile and feedback data.
        Args:
            user_profile: The user's profile data
            feedback_result: The result of processing user feedback
        Returns:
            Dictionary containing generated rules and any relevant metadata
        """
        # Load data from all sources
        user_data = self._load_user_data(user_profile)
        workout_data = self._load_workout_data()
        nutrition_data = self._load_nutrition_data(user_profile)
        progress_data = self._load_progress_data(user_profile)
        feedback_data = self._load_feedback_data(user_profile)

        # Prepare prompt for LLM
        formatted_prompt = self.prompt.format(
            user_profile=user_profile,
            workout_data=workout_data,
            nutrition_data=nutrition_data,
            progress_data=progress_data,
            feedback_data=feedback_data
        )

        # Generate rules using LLM
        response = self.llm.invoke(formatted_prompt)

        # Parse and return the generated rules
        return {
            "rules": response.strip(),
            "metadata": {
                "user_id": user_profile.get("name"),
                "context": "dynamic_rule_generation"
            }
        }

    def _load_user_data(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Load user data from the profile."""
        return user_profile

    def _load_workout_data(self) -> List[Dict[str, Any]]:
        """Load workout data from CSV file."""
        workout_data = []
        try:
            with open('data/workouts.csv', mode='r') as file:
                reader = csv.DictReader(file)
                workout_data = [row for row in reader]
        except FileNotFoundError:
            print("Workout data file not found. Using default workout data.")
        return workout_data

    def _load_nutrition_data(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Load nutrition data based on user profile."""
        # This is a placeholder; actual implementation would fetch data from Nutrition API or local storage
        return user_profile.get("nutrition_plan", {})

    def _load_progress_data(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Load progress data for the user."""
        progress_data = []
        try:
            with open('data/progress_data.csv', mode='r') as file:
                reader = csv.DictReader(file)
                progress_data = [row for row in reader if row['user_id'] == user_profile.get("name")]
        except FileNotFoundError:
            print("Progress data file not found.")
        return progress_data

    def _load_feedback_data(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Load feedback data for the user."""
        feedback_data = []
        try:
            with open('data/feedback_data.json', 'r') as file:
                data = json.load(file)
                feedback_data = data.get(user_profile.get("name"), [])
        except FileNotFoundError:
            print("Feedback data file not found.")
        return feedback_data
