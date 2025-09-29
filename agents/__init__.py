# Handles user profile information such as age, weight, height, goals, etc.
from .profile_agent import ProfileAgent

# Responsible for generating or managing personalized workout plans
from .workout_agent import WorkoutAgent

# Manages dietary recommendations and nutrition tracking
from .nutrition_agent import NutritionAgent

# Tracks user progress over time (e.g., weight loss, strength gains)
from .progress_agent import ProgressAgent

# Collects and processes user feedback to adapt plans or improve service
from .feedback_agent import FeedbackAgent

# Coordinates actions between different agents to ensure consistency and synergy
from .coordinator_agent import CoordinatorAgent

# Dynamically generates rules or logic based on user behavior or feedback
from .dynamic_rule_generator import DynamicRuleGenerator

