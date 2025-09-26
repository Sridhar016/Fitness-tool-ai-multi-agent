# agents/coordinator_agent.py
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any
from agents.base_agent import BaseAgent

class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.profile_file = os.path.join("data", "user_profiles.json")
        self._initialize_data_files()

    def _initialize_data_files(self) -> None:
        """Initialize all required data files."""
        # Initialize user profiles if not exists
        if not os.path.exists(self.profile_file):
            with open(self.profile_file, 'w') as f:
                json.dump({}, f)

    def resolve_conflicts(self, profile_data: Dict[str, Any], feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve conflicts between profile constraints and feedback suggestions.
        Enhanced with 7-day plan context and collaboration with other agents.
        """
        user_id = profile_data.get("name", "Unknown")
        conflicts = []
        resolutions = []

        # Log initial conflict check
        self.log_decision(
            user_id=user_id,
            action="Checking for conflicts",
            metadata={
                "profile": profile_data,
                "feedback": feedback_data
            }
        )

        # 1. Check for intensity conflicts with injuries
        if "increase_intensity" in feedback_data.get("suggested_action", "").lower() and "injury" in profile_data.get("preferences", "").lower():
            conflicts.append("Increase intensity conflicts with injury status")
            resolutions.append({
                "adjustment": "Decrease intensity and suggest low-impact exercises",
                "safe_fallback": "Swap high-impact exercises with cycling or swimming",
                "priority": "high"
            })

        # 2. Check for nutrition conflicts with preferences
        if "high_protein" in feedback_data.get("nutrition_suggestions", "").lower() and "vegan" in profile_data.get("preferences", "").lower():
            conflicts.append("High protein suggestion conflicts with vegan preference")
            resolutions.append({
                "adjustment": "Suggest plant-based protein sources",
                "safe_fallback": "Increase lentils, tofu, and quinoa in meal plan",
                "priority": "medium"
            })

        # 3. Check for workout type conflicts
        if "running" in feedback_data.get("suggested_exercises", "").lower() and "no_running" in profile_data.get("preferences", "").lower():
            conflicts.append("Running suggestion conflicts with user preference")
            resolutions.append({
                "adjustment": "Replace running with cycling or swimming",
                "safe_fallback": "Use elliptical machine as alternative",
                "priority": "medium"
            })

        # Log conflicts and resolutions
        self.log_decision(
            user_id=user_id,
            action="Conflicts resolved",
            metadata={
                "conflicts": conflicts,
                "resolutions": resolutions
            }
        )

        return {
            "conflicts": conflicts,
            "resolutions": resolutions,
            "status": "resolved" if resolutions else "none"
        }

    def manage_workflow(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main workflow management with 7-day plan cycle handling.
        Coordinates all agents and manages plan generation.
        """
        user_id = user_profile.get("name", "Unknown")
        self.log_decision(
            user_id=user_id,
            action="Starting workflow coordination",
            metadata={"user_profile": user_profile}
        )

        # Check current plan status
        plan_status = self._check_plan_status(user_id)

        result = {
            'status': 'success',
            'user_id': user_id,
            'plan_status': plan_status,
            'actions': [],
            'conflicts': [],
            'resolutions': []
        }

        # Handle plan generation based on status
        if plan_status.get('can_generate_new', False):
            # Generate new plans
            result.update(self._generate_new_plans(user_profile))
        else:
            # Check existing plan
            result.update(self._check_existing_plan(user_id))

        # Log final workflow result
        self.log_decision(
            user_id=user_id,
            action="Workflow completed",
            metadata={
                "status": result['status'],
                "plan_action": result.get('plan_action', 'none')
            }
        )

        return result

    def _check_plan_status(self, user_id: str) -> Dict[str, Any]:
        """Check if user can generate new plans or has active plans."""
        try:
            # Load user profile
            with open(self.profile_file, 'r') as f:
                profiles = json.load(f)
            user_profile = profiles.get(user_id, {})

            # Check plan status
            plan_start = user_profile.get('plan_start_date')
            plan_end = user_profile.get('plan_end_date')

            if not plan_start:
                # No active plan
                return {
                    'has_active_plan': False,
                    'can_generate_new': True,
                    'status': 'no_plan'
                }

            # Check if plan is still active
            if datetime.fromisoformat(plan_end) > datetime.now():
                # Active plan exists
                days_left = (datetime.fromisoformat(plan_end) - datetime.now()).days
                return {
                    'has_active_plan': True,
                    'can_generate_new': False,
                    'status': 'active_plan',
                    'days_remaining': days_left
                }

            # Plan has expired
            return {
                'has_active_plan': False,
                'can_generate_new': True,
                'status': 'expired_plan'
            }

        except Exception as e:
            self.log_decision(user_id, f"Plan status check failed: {e}")
            return {
                'has_active_plan': False,
                'can_generate_new': True,
                'status': 'error',
                'error': str(e)
            }

    def _generate_new_plans(self, user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate generation of new 7-day plans."""
        user_id = user_profile.get("name", "Unknown")
        self.log_decision(
            user_id=user_id,
            action="Generating new 7-day plans"
        )

        try:
            # In a real implementation, this would call the actual agent methods
            # For now, we'll simulate the coordination
            workout_result = {
                'status': 'success',
                'plan': {
                    'day_1': {'exercises': ['Push-ups', 'Squats', 'Running']},
                    'day_2': {'exercises': ['Pull-ups', 'Lunges', 'Cycling']},
                },
                'start_date': datetime.now().isoformat(),
                'end_date': (datetime.now() + timedelta(days=7)).isoformat()
            }

            nutrition_result = {
                'status': 'success',
                'plan': {
                    'day_1': {'meals': ['Oatmeal', 'Chicken Salad', 'Fish with Veggies']},
                    'day_2': {'meals': ['Smoothie', 'Quinoa Bowl', 'Tofu Stir-fry']},
                }
            }

            # Update user profile with new plans
            self._update_user_plans(user_id, workout_result, nutrition_result)

            return {
                'plan_action': 'generated_new_plans',
                'workout_plan': workout_result,
                'nutrition_plan': nutrition_result,
                'status': 'new_plans_generated'
            }

        except Exception as e:
            self.log_decision(user_id, f"Plan generation failed: {e}")
            return {
                'status': 'error',
                'plan_action': 'generation_failed',
                'error': str(e)
            }

    def _check_existing_plan(self, user_id: str) -> Dict[str, Any]:
        """Check and manage existing active plan."""
        try:
            # Get progress (in real implementation, this would come from ProgressAgent)
            progress = self._get_plan_progress(user_id)

            return {
                'plan_action': 'checked_existing_plan',
                'progress': progress,
                'status': 'plan_active',
                'message': f"Active plan with {progress.get('days_remaining', 0)} days remaining"
            }

        except Exception as e:
            self.log_decision(user_id, f"Existing plan check failed: {e}")
            return {
                'status': 'error',
                'plan_action': 'progress_check_failed',
                'error': str(e)
            }

    def _update_user_plans(self, user_id: str, workout_plan: Dict[str, Any], nutrition_plan: Dict[str, Any]) -> None:
        """Update user profile with new plans."""
        try:
            with open(self.profile_file, 'r') as f:
                profiles = json.load(f)

            profiles[user_id] = {
                'plan_start_date': datetime.now().isoformat(),
                'plan_end_date': (datetime.now() + timedelta(days=7)).isoformat(),
                'workout_plan': workout_plan.get('plan', {}),
                'nutrition_plan': nutrition_plan.get('plan', {}),
                'plan_id': f"plan_{datetime.now().strftime('%Y%m%d')}",
                'last_updated': datetime.now().isoformat()
            }

            with open(self.profile_file, 'w') as f:
                json.dump(profiles, f, indent=2)

            self.log_decision(
                user_id=user_id,
                action="Updated user plans"
            )

        except Exception as e:
            self.log_decision(user_id, f"Failed to update plans: {e}")

    def _get_plan_progress(self, user_id: str) -> Dict[str, Any]:
        """Get current plan progress (simulated)."""
        # In real implementation, this would come from ProgressAgent
        return {
            'days_completed': 3,
            'days_remaining': 4,
            'completion_percentage': 43,
            'last_logged': datetime.now().isoformat()
        }
