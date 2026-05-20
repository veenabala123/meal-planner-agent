from graph import app
from nodes import save_meal_plan

def run_week(week_number, previous_weeks=None):
    """Run the agent for one week."""

    if previous_weeks is None:
        previous_weeks = []

    print(f"\n{'='*50}")
    print(f"  GENERATING MEAL PLAN — WEEK {week_number}")
    print(f"{'='*50}\n")

    # This is the initial state we feed into the graph
    initial_state = {
        "proteins": ["chicken", "fish", "shrimp"],
        "restrictions": ["no beef", "no pork"],
        "cuisines": ["Indian", "Mediterranean", "Mexican", "East Asian", "American comfort"],
        "spice_level": "medium",
        "week_number": week_number,
        "current_meals": [],
        "previous_weeks": previous_weeks,
        "rotation_valid": False,
        "balance_valid": False,
        "retry_count": 0,
        "swap_requested": False,
    }

    # RUN THE GRAPH — this one line does everything!
    result = app.invoke(initial_state)

    # Display results
    print(f"\n{'='*50}")
    print(f"  WEEK {week_number} MEAL PLAN")
    print(f"{'='*50}\n")

    for meal in result["current_meals"]:
        emoji = "🍱" if meal["type"] == "lunch" else "🍽️"
        print(f"  {emoji} {meal['name']}")
        print(f"     {meal['type'].upper()} | {meal['cuisine']} | {meal['protein']}")
        print(f"     {meal.get('protein_grams', '?')}g protein | {meal.get('calories', '?')} cal | {meal.get('cook_time_min', '?')} min")
        print()

    return result["current_meals"]


# === RUN IT! ===

# Week 1 — no history
week1_meals = run_week(1)
save_meal_plan(week1_meals, 1)

# Week 2 — pass week 1 as history so rotation checker works
week2_meals = run_week(2, previous_weeks=[week1_meals])
save_meal_plan(week2_meals, 2)