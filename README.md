An AI-powered weekly meal planner built with LangGraph and Claude (Anthropic). This project demonstrates core agentic AI concepts : state management, tool use, conditional routing, validation loops, and human in the loop interaction, through a practical meal planning use case.

### What It Does

- Generates 2 lunches + 2 dinners per week, personalized to your dietary preferences
- Ensures a 3 week rotation so meals don't repeat too soon
- Validates nutritional balance (minimum 25g protein per meal)
- Supports meal swapping  reject any meal and get an AI generated replacement (human in the loop)
- Saves meal plans to a JSON file with dates for future reference
- Lunches are lunchbox friendly dishes

```
meal-planner-agent/
├── state.py            # State definition (TypedDict) — the shared memory
├── nodes.py            # Node functions — generate, validate, swap, save
├── graph.py            # Graph wiring — nodes + edges + conditional routing
├── main.py             # Entry point — runs the agent for Week 1 and Week 2
├── meal_plans.json     # Auto-generated — saved meal plans with dates
├── .env                # Your Anthropic API key (not tracked in git)
├── .gitignore          # Keeps .env, venv, and __pycache__ out of git
└── requirements.txt    # Python dependencies
```
### Getting Started

Prerequisites:
- Python 3.10+
- An Anthropic API key

### Installation

### Clone the repo
```
git clone https://github.com/veenabala123/meal-planner-agent.git
cd meal-planner-agent
```

### Create and activate a virtual environment
```
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate          # Windows
```

### Install dependencies
```
pip install langgraph langchain-anthropic python-dotenv
```

### Configuration
- Create a .env file in the project root:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Run It
```
python main.py
```

### View Your Meal Plans
Open meal-viewer.html in your browser to see a visual dashboard of your saved plans:
```
open meal-viewer.html
```