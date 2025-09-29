import os
import csv
import json
from typing import Dict, Any, List
from datetime import datetime
import pandas as pd
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from agents.base_agent import BaseAgent

class ProgressAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.llm = Ollama(model=os.getenv("OLLAMA_MODEL", "llama3.2"))
        self.data_file = 'data/progress_data.csv'
        self.profile_file = 'data/user_profiles.json'
        self._init_files()

    def _init_files(self):
        """Initialize files with proper permissions"""
        os.makedirs('data', exist_ok=True)

        # Initialize CSV with essential fields
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'user_id', 'timestamp', 'day', 'weight', 'height',
                    'workout_completed', 'duration_min', 'calories_burned',
                    'waist', 'chest'
                ])

        # Initialize JSON file if not exists
        if not os.path.exists(self.profile_file):
            with open(self.profile_file, 'w') as f:
                json.dump({}, f)

    def get_form(self) -> Dict[str, Any]:
        """Progress input form structure"""
        return {
            "weight": {"type": "number", "label": "Weight (kg)", "required": True},
            "height": {"type": "number", "label": "Height (cm)"},
            "workout_completed": {"type": "boolean", "label": "Completed Workout", "default": True},
            "duration_min": {"type": "number", "label": "Duration (min)", "default": 30},
            "calories_burned": {"type": "number", "label": "Calories Burned", "default": 200},
            "body_measurements": {
                "type": "object", "label": "Body Measurements (cm)",
                "fields": {
                    "waist": {"type": "number", "label": "Waist"},
                    "chest": {"type": "number", "label": "Chest"}
                }
            }
        }

    def log_progress(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log workout progress with timestamp"""
        try:
            # Prepare data with proper values
            entry = {
                'user_id': user_id,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'day': self._next_day(user_id),
                'weight': data.get('weight'),
                'height': data.get('height'),
                'workout_completed': data.get('workout_completed', True),
                'duration_min': data.get('duration_min'),
                'calories_burned': data.get('calories_burned'),
                'waist': data.get('body_measurements', {}).get('waist'),
                'chest': data.get('body_measurements', {}).get('chest')
            }

            # Write to CSV with separate columns for each metric
            with open(self.data_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'user_id', 'timestamp', 'day', 'weight', 'height',
                    'workout_completed', 'duration_min', 'calories_burned',
                    'waist', 'chest'
                ])
                writer.writerow(entry)

            # Update profile
            self._update_profile(user_id, entry)
            return {'status': 'success', 'message': 'Progress logged'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _next_day(self, user_id: str) -> int:
        """Get next day in 7-day cycle"""
        try:
            if not os.path.exists(self.data_file):
                return 1

            df = pd.read_csv(self.data_file)
            user_data = df[df['user_id'] == user_id]

            if user_data.empty:
                return 1

            days = user_data['day'].dropna().astype(int).unique()
            return next((d for d in range(1, 8) if d not in days), 1)
        except:
            return 1

    def _update_profile(self, user_id: str, entry: Dict[str, Any]):
        """Update user profile with progress"""
        try:
            profiles = {}
            if os.path.exists(self.profile_file):
                with open(self.profile_file, 'r') as f:
                    profiles = json.load(f)

            if user_id not in profiles:
                profiles[user_id] = {'progress': []}

            profiles[user_id]['progress'].append({
                'timestamp': entry['timestamp'],
                'day': entry['day'],
                'data': {
                    'weight': entry.get('weight'),
                    'height': entry.get('height'),
                    'workout_completed': entry.get('workout_completed'),
                    'duration_min': entry.get('duration_min'),
                    'calories_burned': entry.get('calories_burned'),
                    'waist': entry.get('waist'),
                    'chest': entry.get('chest')
                }
            })

            with open(self.profile_file, 'w') as f:
                json.dump(profiles, f, indent=2)
        except:
            pass

    def load_progress(self, user_id: str) -> List[Dict[str, Any]]:
        """Load user progress data"""
        try:
            if not os.path.exists(self.data_file):
                return []

            df = pd.read_csv(self.data_file)
            user_data = df[df['user_id'] == user_id]

            # Convert to list of dicts
            records = user_data.to_dict('records')

            # Add body_measurements field for backward compatibility
            for record in records:
                record['body_measurements'] = {
                    'waist': record.get('waist'),
                    'chest': record.get('chest')
                }

            return records
        except Exception as e:
            print(f"Error loading progress: {e}")
            return []

    def get_summary(self, user_id: str) -> Dict[str, Any]:
        """Get progress summary with trends"""
        try:
            progress = self.load_progress(user_id)
            if not progress:
                return {'error': 'No data'}

            # Get last entry for display
            last_entry = progress[-1] if progress else None

            # Calculate trends
            trends = self._analyze_trends(progress)

            return {
                'last_entry': {
                    'timestamp': last_entry.get('timestamp') if last_entry else None,
                    'weight': last_entry.get('weight') if last_entry else None,
                    'height': last_entry.get('height') if last_entry else None,
                    'duration_min': last_entry.get('duration_min') if last_entry else None,
                    'calories_burned': last_entry.get('calories_burned') if last_entry else None,
                    'waist': last_entry.get('waist') if last_entry else None,
                    'chest': last_entry.get('chest') if last_entry else None
                },
                'recent_progress': progress[-5:] if len(progress) > 0 else [],
                'trends': trends,
                'total_sessions': len(progress)
            }
        except Exception as e:
            print(f"Error getting summary: {e}")
            return {'error': 'Analysis failed'}

    def _analyze_trends(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate fitness trends"""
        df = pd.DataFrame(data)
        trends = {}

        # Weight trend
        if 'weight' in df.columns and not df['weight'].isna().all():
            weights = df.dropna(subset=['weight'])
            if len(weights) >= 2:
                start, end = weights.iloc[0]['weight'], weights.iloc[-1]['weight']
                change = end - start
                trends['weight'] = {
                    'start': start, 'end': end,
                    'change_kg': round(change, 2),
                    'change_percent': round((change/start)*100, 2) if start else 0
                }

        # Body measurement trends
        for measure in ['waist', 'chest']:
            if measure in df.columns and not df[measure].isna().all():
                measurements = df.dropna(subset=[measure])
                if len(measurements) >= 2:
                    start, end = measurements.iloc[0][measure], measurements.iloc[-1][measure]
                    change = end - start
                    trends[measure] = {
                        'start': start, 'end': end,
                        'change': round(change, 2),
                        'change_percent': round((change/start)*100, 2) if start else 0
                    }

        # Completion rate
        if 'workout_completed' in df.columns:
            trends['completion_rate'] = round(df['workout_completed'].mean() * 100)

        return trends
