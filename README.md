# AI Fitness Coach

An intelligent multi-agent system for personalized fitness and nutrition recommendations.

## 📌 About The Project

AI Fitness Coach is a multi-agent system that generates personalized workout and nutrition plans based on individual user profiles. The system adapts to user feedback, resolves conflicts between constraints, and tracks progress over time.

### Key Features

- ✅ **Personalized Plan Generation** - Creates tailored workout and nutrition plans
- ✅ **Adaptive Feedback System** - Adjusts plans based on user input
- ✅ **Conflict Resolution** - Handles conflicting user preferences
- ✅ **Progress Tracking** - Monitors and visualizes fitness progress
- ✅ **Multi-Agent Architecture** - Specialized agents for each function

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip package manager
- Git
- Ollama (for local LLM functionality)

### Installation

1. Clone the repo
```bash
git clone https://github.com/Sridhar016/Fitness-tool-ai-multi-agent.git
```

2. Install Ollama and pull the required model:
```bash
# Install Ollama from https://ollama.ai/
ollama pull llama3.2
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

### Usage
1. Start the Ollama service:
```bash
ollama serve
```
  
2. In a separate terminal, run the application:
```bash
streamlit run app.py
```
  
3. Create a user profile with your fitness goals
4. Generate personalized plans
5. Track your progress and provide feedback

### 📂 Project Structure
```bash
.
├── app.py                # Main application
├── agents/               # Agent implementations
│   ├── __init__.py
│   ├── base_agent.py
│   ├── coordinator_agent.py
│   ├── dynamic_rule_generator.py
│   ├── feedback_agent.py
│   ├── nutrition_agent.py
│   ├── orchestrator.py
│   ├── profile_agent.py
│   ├── progress_agent.py
│   └── workout_agent.py
├── data/                 # Data storage
│   ├── agent_logs.json
│   ├── feedback_data.json
│   ├── progress_data.csv
│   ├── user_profiles.json
│   └── workouts.csv
├── requirements.txt      # Dependencies
└── README.md             # Project documentation
```

### 🛠 Built With

- Python
- Streamlit
- Ollama - Local LLM


