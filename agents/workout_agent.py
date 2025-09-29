import os
import csv
from typing import Dict, Any, List, Optional
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from agents.base_agent import BaseAgent

class WorkoutAgent(BaseAgent):
    def __init__(self):
        model = os.getenv("OLLAMA_MODEL", "llama3.2")
        self.llm = Ollama(model=model)
        self.workout_data = self._load_workout_data()
        self.prompt = PromptTemplate(
            input_variables=["goal", "level", "preferences","filtered_exercises"],
            template=(
                "You are a professional fitness coach.\n"
                "Generate a **structured 7-day workout plan** for the user as detailed readable text.\n"
                "Here is a list of exercises you should use:\n"
                "{filtered_exercises}\n\n"
                "Take into account the following conflict resolutions:\n"
                "{conflict_resolutions}\n"
                "And the following dynamic rules:\n"
                "{dynamic_rules}\n\n"
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

    def _filter_exercises(
        self,
        user_profile: Dict[str, Any],
        conflict_resolutions: Optional[List[Dict[str, Any]]] = None,
        dynamic_rules: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Filter exercises based on user profile, conflict resolutions, and dynamic rules.
        """
        filtered_exercises = []
        preferences = user_profile.get("preferences", "").lower()
        level = user_profile.get("level", "Beginner").lower()

        for exercise in self.workout_data:
            # Filter by fitness level
            if level == "beginner" and exercise.get("Difficulty", "").lower() != "beginner":
                continue
            elif level == "intermediate" and exercise.get("Difficulty", "").lower() == "advanced":
                continue
            elif level == "advanced" and exercise.get("Difficulty", "").lower() not in ["advanced", "intermediate"]:
                continue
            # Filter by injury risk
            if "injury" in preferences and exercise.get("InjuryRisk", "").lower() == "high":
                continue
            # Filter by user preferences
            if "no running" in preferences and exercise.get("ExerciseName", "").lower() == "running":
                continue
            filtered_exercises.append(exercise)

        # Apply conflict resolutions
        if conflict_resolutions:
            for resolution in conflict_resolutions:
                if resolution.get("adjustment") == "Decrease intensity and suggest low-impact exercises":
                    filtered_exercises = [
                        ex for ex in filtered_exercises
                        if ex.get("InjuryRisk", "").lower() in ["low", "medium"]
                    ]
                elif resolution.get("adjustment") == "Suggest low-intensity exercises":
                    filtered_exercises = [
                        ex for ex in filtered_exercises
                        if ex.get("Difficulty", "").lower() in ["beginner"]
                    ]
                elif resolution.get("adjustment") == "Suggest indoor workouts":
                    filtered_exercises = [
                        ex for ex in filtered_exercises
                        if ex.get("Equipment", "").lower() != "none" or
                           ex.get("ExerciseName", "").lower() in ["yoga", "push-ups", "squats"]
                    ]

        # Format for prompt
        exercises_str = "\n".join(
            f"- {exercise['ExerciseName']}: Targets {exercise['BodyPart']}, "
            f"Equipment: {exercise['Equipment']}, "
            f"Difficulty: {exercise['Difficulty']}, "
            f"Injury Risk: {exercise['InjuryRisk']}"
            for exercise in filtered_exercises
        )
        return exercises_str

    def generate_plan(
        self,
        user_profile: Dict[str, Any],
        conflict_resolutions: Optional[List[Dict[str, Any]]] = None,
        dynamic_rules: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a full detailed 7-day workout plan as readable text.
        """
        preferences = user_profile.get("preferences", "none")
        filtered_exercises = self._filter_exercises(
            user_profile, conflict_resolutions, dynamic_rules
        )
        formatted_prompt = self.prompt.format(
            goal=user_profile.get("goal", "general fitness"),
            level=user_profile.get("level", "Beginner"),
            preferences=preferences,
            filtered_exercises=filtered_exercises,
            conflict_resolutions=str(conflict_resolutions),
            dynamic_rules=str(dynamic_rules)
        )
        try:
            response = self.llm.invoke(formatted_prompt)
            return response.strip()
        except Exception as e:
            return f"Failed to generate workout plan: {e}"