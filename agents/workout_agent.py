import os
import csv
from typing import Dict, Any, List
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate

class WorkoutAgent:
    def __init__(self):
        model = os.getenv("OLLAMA_MODEL", "llama3.2")
        self.llm = Ollama(model=model)
        self.workout_data = self._load_workout_data()
        self.prompt = PromptTemplate(
            input_variables=["goal", "level", "preferences", "filtered_exercises"],
            template=(
                "You are a professional fitness coach.\n"
                "Generate a **structured 7-day workout plan** for the user as detailed readable text.\n"
                "Use the following exercises as a reference:\n"
                "{filtered_exercises}\n"
                "Include:\n"
                "- Time of day recommendation (morning/evening)\n"
                "- Warm-up exercises\n"
                "- Main exercises with sets, reps, rest, and tips\n"
                "- Cooldown / stretching\n"
                "- Daily suggestions and tips\n"
                "- Progression advice for next week\n\n"
                "User Goal: {goal}\n"
                "Fitness Level: {level}\n"
                "Preferences: {preferences}\n\n"
                "Return ONLY human-readable text. Do NOT use JSON."
            )
        )

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

    def _filter_exercises(self, user_profile: Dict[str, Any]) -> str:
        """Filter exercises based on user preferences and constraints."""
        filtered_exercises = []
        preferences = user_profile.get("preferences", "").lower()
        level = user_profile.get("level", "Beginner").lower()

        for exercise in self.workout_data:
            # Filter based on fitness level
            if level == "beginner" and exercise.get("Difficulty", "").lower() != "beginner":
                continue
            elif level == "intermediate" and exercise.get("Difficulty", "").lower() == "advanced":
                continue
            elif level == "advanced" and exercise.get("Difficulty", "").lower() not in ["advanced", "intermediate"]:
                continue

            # Filter based on injury risk
            if "injury" in preferences and exercise.get("InjuryRisk", "").lower() == "high":
                continue

            # Filter based on body part or equipment preferences
            if "no running" in preferences and exercise.get("ExerciseName", "").lower() == "running":
                continue

            filtered_exercises.append(exercise)

        # Format filtered exercises for the prompt
        exercises_str = "\n".join(
            f"- {exercise['ExerciseName']}: Targets {exercise['BodyPart']}, "
            f"Equipment: {exercise['Equipment']}, "
            f"Difficulty: {exercise['Difficulty']}"
            for exercise in filtered_exercises
        )
        return exercises_str

    def generate_plan(self, user_profile: Dict[str, Any]) -> str:
        """
        Generate a full detailed 7-day workout plan directly as readable text.
        """
        preferences = user_profile.get("preferences", "none")
        filtered_exercises = self._filter_exercises(user_profile)
        formatted_prompt = self.prompt.format(
            goal=user_profile.get("goal", "general fitness"),
            level=user_profile.get("level", "Beginner"),
            preferences=preferences,
            filtered_exercises=filtered_exercises
        )
        try:
            response = self.llm.invoke(formatted_prompt)
            return response.strip()
        except Exception as e:
            return f"Failed to generate workout plan: {e}"
