import sys
import os
import streamlit as st
import json
from dotenv import load_dotenv
from agents.orchestrator import Orchestrator
from datetime import datetime

# Load environment variables
load_dotenv()
orchestrator = Orchestrator()

# App title
st.title("AI Multi-Agent Fitness Coach")

# Initialize data directory and files
os.makedirs("data", exist_ok=True)

# ---------------- Sidebar: Profile Management ----------------
with st.sidebar:
    st.header("User Profile")
    # Load all profiles
    profiles_data = orchestrator.profile_agent.load_user_profile()
    usernames = list(profiles_data.keys())

    # Initialize session state for selected_user if it doesn't exist
    if "selected_user" not in st.session_state:
        st.session_state.selected_user = "New User"

    # Dropdown to select user
    selected_user = st.selectbox(
        "Select User", ["New User"] + usernames, index=0
    )
    st.session_state.selected_user = selected_user  # Update session state

    if st.session_state.selected_user == "New User":
        # New user input form
        st.subheader("Create New Profile")
        name = st.text_input("Name")
        age = st.number_input("Age", 12, 100, 25)
        goal = st.selectbox("Goal", ["Fat Loss", "Muscle Gain", "Endurance", "General Fitness"])
        level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"])
        preferences = st.text_input("Preferences (e.g., 'No running, prefers weightlifting')", "None")
        health_info = st.text_input("Health Information (e.g., allergies, medical conditions)", "None")
        meal_preference = st.selectbox("Meal Preference", ["Non-Veg", "Vegeatarian", "Vegan", "Gluten-Free", "Other"])
        


        if st.button("Save Profile"):
            if not name:
                st.warning("Name is required!")
            else:
                profile_data = {
                    "name": name,
                    "age": age,
                    "goal": goal,
                    "level": level,
                    "preferences": preferences,
                    "health_info": health_info,
                    "meal_preference": meal_preference
                }
                orchestrator.profile_agent.update_profile({name: profile_data})
                st.success(f"Profile '{name}' saved!")
                st.session_state.selected_user = name  # Update selection
                st.rerun()  # Rerun to reflect the new user in the dropdown
    else:
        # Display selected user's profile in a readable format
        st.subheader("User Details")
        profile_data = profiles_data[st.session_state.selected_user]

        # Display profile details as a clean list
        st.markdown(
            f"""
            - **Name:** {profile_data.get('name', 'N/A')}
            - **Age:** {profile_data.get('age', 'N/A')}
            - **Goal:** {profile_data.get('goal', 'N/A')}
            - **Fitness Level:** {profile_data.get('level', 'N/A')}
            - **Preferences:** {profile_data.get('preferences', 'None')}
            - **Health Info:** {profile_data.get('health_info', 'None')}
            - **Meal Preference:** {profile_data.get('meal_preference', 'None')}
            """
        )

# ---------------- Main Page: Workflow ----------------
if "selected_user" in st.session_state and st.session_state.selected_user != "New User":
    # Reload profiles_data to ensure it's up-to-date
    profiles_data = orchestrator.profile_agent.load_user_profile()
    if st.session_state.selected_user in profiles_data:
        profile_data = profiles_data[st.session_state.selected_user]
        st.subheader(f"Welcome, {profile_data['name']}!")

        # Add tabs for better organization
        tab1, tab2, tab3 = st.tabs(["Generate Plans", "Log Progress", "View Progress"])

        with tab1:
            if st.button("Generate Plans"):
                with st.spinner("Generating your personalized plans..."):
                    result = orchestrator.run(profile_data)
                    st.subheader("Workout Plan")
                    st.text(result["workout_text"])

                    st.subheader("Nutrition Plan")
                    if result["nutrition_json"] and "meal_plan" in result["nutrition_json"]:
                        for meal in result["nutrition_json"]["meal_plan"]:
                            st.write(f"**{meal.get('type', '')}**: {meal.get('description', '')}")
                            st.write(f"  → {meal.get('calories', 'N/A')} kcal | "
                                    f"Protein: {meal.get('protein', 'N/A')}g | "
                                    f"Carbs: {meal.get('carbs', 'N/A')}g | "
                                    f"Fat: {meal.get('fat', 'N/A')}g")
                            st.write("")  # Add space between meals
                    else:
                        st.text(result["nutrition_text"])

        with tab2:
            st.subheader("Log Your Daily Progress")

            with st.form("progress_form"):
                st.write("### Today's Progress")

                # Basic metrics
                weight = st.number_input(
                    "Current Weight (kg)",
                    value=70.0,
                    step=0.1
                )

                height = st.number_input(
                    "Height (cm)",
                    min_value=100.0,
                    max_value=250.0,
                    value=170.0,
                    step=0.1
                )

                # Workout details
                workout_completed = st.checkbox(
                    "Completed Workout",
                    value=True
                )

                duration_min = st.number_input(
                    "Workout Duration (minutes)",
                    min_value=0,
                    value=30
                )

                calories_burned = st.number_input(
                    "Calories Burned",
                    min_value=0,
                    value=200
                )

                # Body measurements
                st.write("### Body Measurements (cm)")
                waist = st.number_input(
                    "Waist",
                    min_value=50.0,
                    max_value=150.0,
                    value=80.0,
                    step=0.1
                )

                chest = st.number_input(
                    "Chest",
                    min_value=60.0,
                    max_value=150.0,
                    value=90.0,
                    step=0.1
                )

                if st.form_submit_button("Log Progress"):
                    progress_data = {
                        'weight': weight,
                        'height': height,
                        'workout_completed': workout_completed,
                        'duration_min': duration_min,
                        'calories_burned': calories_burned,
                        'body_measurements': {
                            'waist': waist,
                            'chest': chest
                        }
                    }

                    result = orchestrator.progress_agent.log_progress(
                        profile_data["name"],
                        progress_data
                    )

                    if result['status'] == 'success':
                        st.success("Progress logged successfully!")
                        st.rerun()  # Refresh to show updated progress
                    else:
                        st.error(f"Error: {result['message']}")

        with tab3:
            st.subheader("Your Progress Summary")

            # Get progress summary
            summary = orchestrator.progress_agent.get_summary(profile_data["name"])

            if 'error' in summary:
                st.warning(summary['error'])
            elif 'last_entry' in summary and summary['last_entry']:
                last_entry = summary['last_entry']

                st.write("### Last Workout Entry")
                st.write(f"""
                - **Date/Time:** {last_entry.get('timestamp', 'N/A')}
                - **Weight:** {last_entry.get('weight', 'N/A')} kg
                - **Height:** {last_entry.get('height', 'N/A')} cm
                - **Duration:** {last_entry.get('duration_min', 'N/A')} minutes
                - **Calories Burned:** {last_entry.get('calories_burned', 'N/A')}
                """)

                # Display body measurements if they exist
                st.write("**Body Measurements:**")
                st.write(f"- Waist: {last_entry.get('waist', 'N/A')} cm")
                st.write(f"- Chest: {last_entry.get('chest', 'N/A')} cm")

                # Show trends if available
                if 'trends' in summary:
                    st.write("### Your Progress Trends")

                    # Weight trend
                    if 'weight' in summary['trends']:
                        weight_trend = summary['trends']['weight']
                        st.metric(
                            "Weight Change",
                            f"{weight_trend['change_kg']} kg",
                            f"{weight_trend['change_percent']}%"
                        )

                    # Body measurement trends
                    for measure in ['waist', 'chest']:
                        if measure in summary['trends']:
                            trend = summary['trends'][measure]
                            st.metric(
                                f"{measure.capitalize()} Change",
                                f"{trend['change']} cm",
                                f"{trend['change_percent']}%"
                            )

                # Show recent progress (simplified to just show time and duration)
                st.write("### Recent Workouts")
                if 'recent_progress' in summary and summary['recent_progress']:
                    for entry in summary['recent_progress']:
                        st.write(f"- {entry.get('timestamp', 'N/A')}: {entry.get('duration_min', 'N/A')} minutes")
                else:
                    st.write("No recent progress data available.")
            else:
                st.write("No progress data yet. Please log your first workout!")

        # Feedback section
        st.subheader("Feedback")
        feedback_text = st.text_area("Your Feedback")
        if st.button("Submit Feedback"):
            if feedback_text.strip():
                result = orchestrator.run(profile_data, feedback_text=feedback_text)
                st.success("✅ Feedback stored and plans updated!")

                # Show updated plans
                with st.expander("Updated Workout Plan"):
                    st.text(result["workout_text"])

                with st.expander("Updated Nutrition Plan"):
                    if result["nutrition_json"] and "meal_plan" in result["nutrition_json"]:
                        for meal in result["nutrition_json"]["meal_plan"]:
                            st.write(f"**{meal.get('type', '')}**: {meal.get('description', '')}")
                            st.write(f"  → {meal.get('calories', 'N/A')} kcal | "
                                    f"Protein: {meal.get('protein', 'N/A')}g | "
                                    f"Carbs: {meal.get('carbs', 'N/A')}g | "
                                    f"Fat: {meal.get('fat', 'N/A')}g")
                            st.write("")  # Add space between meals
                    else:
                        st.text(result["nutrition_text"])

                if result["feedback_result"]:
                    st.info(f"Feedback Agent Response: {result['feedback_result'].get('suggested_action', 'Feedback recorded')}")
                if result.get("conflict_resolution"):
                    st.info(f"Conflict Resolution: {result['conflict_resolution']}")
                if result.get("dynamic_rules"):
                    st.info(f"Dynamic Rules Applied: {result['dynamic_rules']}")
            else:
                st.warning("Please enter feedback.")
    else:
        st.warning("Selected user profile not found. Please select another user.")
        st.session_state.selected_user = "New User"
else:
    st.warning("Select or create a user profile to continue.")
