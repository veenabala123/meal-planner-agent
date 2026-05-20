import os
import json
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from datetime import datetime, timedelta

load_dotenv()

llm = ChatAnthropic(model="claude-sonnet-4-20250514")

def generate_meals(state):
    proteins = ", ".join(state["proteins"])
    restrictions = ", ".join(state["restrictions"])
    cuisines = ", ".join(state["cuisines"])
    spice = state["spice_level"]
    week = state["week_number"]

    avoid_meals = ""
    if state["previous_weeks"]:
        past_names = []
        for week_meals in state["previous_weeks"]:
            for meal in week_meals:
                past_names.append(meal["name"])
        avoid_meals = f"\n\nDo NOT repeat these meals from previous weeks: {', '.join(past_names)}"

    prompt = f"""You are a meal planning agent. Generate a meal plan for Week {week}.

REQUIREMENTS:
- Exactly 2 lunch meals and 2 dinner meals
- Allowed proteins: {proteins}
- Restrictions: {restrictions}
- Spice level: {spice}
- Must include at least 1 Indian dish
- Other cuisines to use: {cuisines}
- Cook time: 30-60 minutes per meal
- High protein, balanced diet{avoid_meals}
- Lunch meals MUST be lunchbox-friendly (no messy/soupy dishes, should reheat well in a microwave, avoid strong-smelling fish)

Respond ONLY with a JSON array of exactly 4 objects. No markdown, no backticks, no extra text.
Each object must have:
- "name": meal name
- "type": "lunch" or "dinner"
- "cuisine": one of the allowed cuisines
- "protein": main protein used
- "calories": estimated calories
- "protein_grams": estimated protein in grams
- "cook_time_min": minutes to cook
- "ingredients": list of 6-8 key ingredients
- "steps": list of 4-6 brief cooking steps"""

    print(f"  Calling Claude to generate Week {week} meals...")
    response = llm.invoke(prompt)

    try:
        meals = json.loads(response.content)
        print(f"  Got {len(meals)} meals!")
        for meal in meals:
            print(f"    - {meal['name']} ({meal['type']}, {meal['cuisine']})")
    except json.JSONDecodeError:
        print("  Failed to parse response, will retry...")
        meals = []

    # Step F: Write back to state
    return {
        "current_meals": meals,
        "retry_count": state["retry_count"] + (0 if meals else 1)
    }

def check_rotation(state):
    """Node 2: Make sure no meals repeat within the 3-week window."""

    meals = state["current_meals"]
    previous_weeks = state["previous_weeks"]

    # If no meals were generated (parsing failed), skip validation
    if not meals:
        print("  Skipping rotation check — no meals to check")
        return {"rotation_valid": False}

    # Collect all meal names from previous weeks
    previous_names = []
    for week_meals in previous_weeks:
        for meal in week_meals:
            previous_names.append(meal["name"].lower())

    # Check each new meal against history
    conflicts = []
    for meal in meals:
        if meal["name"].lower() in previous_names:
            conflicts.append(meal["name"])

    if conflicts:
        print(f"  CONFLICT: These meals were used before: {conflicts}")
        return {"rotation_valid": False}
    else:
        print("  Rotation check PASSED — no repeats!")
        return {"rotation_valid": True}


def validate_balance(state):
    """Node 3: Check cuisine mix and protein levels."""

    meals = state["current_meals"]

    # Check 1: Is there at least one Indian dish?
    cuisines = [meal["cuisine"] for meal in meals]
    has_indian = "Indian" in cuisines

    # Check 2: Are there exactly 2 lunches and 2 dinners?
    lunch_count = sum(1 for m in meals if m["type"] == "lunch")
    dinner_count = sum(1 for m in meals if m["type"] == "dinner")
    correct_split = (lunch_count == 2 and dinner_count == 2)

    # Check 3: Reasonable protein per meal (at least 25g)
    low_protein = [m["name"] for m in meals if m.get("protein_grams", 0) < 25]

    # Report results
    all_good = has_indian and correct_split and not low_protein

    if not has_indian:
        print("  WARNING: No Indian dish in this week's plan")
    if not correct_split:
        print(f"  WARNING: Got {lunch_count} lunches and {dinner_count} dinners (expected 2+2)")
    if low_protein:
        print(f"  WARNING: Low protein meals: {low_protein}")
    if all_good:
        print("  Balance check PASSED!")

    return {"balance_valid": all_good}

def swap_meal(state):
    """Human-in-the-loop: let the user reject and replace a meal."""

    meals = state["current_meals"]

    print("\n  Current meals:")
    for i, meal in enumerate(meals):
        print(f"    [{i}] {meal['name']} ({meal['type']}, {meal['cuisine']})")

    print("\n  Enter the number of the meal to swap (or 'done' to accept all):")
    choice = input("  > ").strip()

    if choice.lower() == "done":
        print("  Plan accepted!")
        return {"swap_requested": False}

    try:
        idx = int(choice)
        old_meal = meals[idx]
    except (ValueError, IndexError):
        print("  Invalid choice — keeping current plan")
        return {"swap_requested": False}

    # Ask Claude for a replacement
    print(f"  Got it — swapping out '{old_meal['name']}'...")

    other_names = [m["name"] for m in meals if m["name"] != old_meal["name"]]

    prompt = f"""Generate exactly 1 replacement {old_meal['type']} meal.

REQUIREMENTS:
- Must be a {old_meal['type']} meal
- Proteins allowed: {', '.join(state['proteins'])}
- Restrictions: {', '.join(state['restrictions'])}
- Spice level: {state['spice_level']}
- Cook time: 30-60 minutes
- High protein, balanced
{"- Must be lunchbox-friendly (reheats well, not messy, no strong-smelling fish)" if old_meal['type'] == 'lunch' else ""}
- Must be DIFFERENT from: {', '.join(other_names + [old_meal['name']])}

Respond ONLY with a single JSON object (no array, no markdown):
{{"name": "...", "type": "{old_meal['type']}", "cuisine": "...", "protein": "...", "calories": 0, "protein_grams": 0, "cook_time_min": 0, "ingredients": [...], "steps": [...]}}"""

    response = llm.invoke(prompt)

    try:
        import json
        new_meal = json.loads(response.content)
        meals[idx] = new_meal
        print(f"  Swapped in: {new_meal['name']} ({new_meal['cuisine']})")
        return {"current_meals": meals, "swap_requested": True}
    except Exception as e:
        print(f"  Swap failed: {e}")
        return {"swap_requested": False}
    
def save_meal_plan(meals, week_number):
    """Save the meal plan to a JSON file with dates."""

    today = datetime.now()
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    week_start = today + timedelta(days=days_until_monday + (week_number - 1) * 7)

    week_record = {
        "week_number": week_number,
        "generated_on": today.strftime("%Y-%m-%d %H:%M"),
        "week_starting": week_start.strftime("%Y-%m-%d (%A)"),
        "meals": meals
    }

    filename = "meal_plans.json"
    try:
        with open(filename, "r") as f:
            all_plans = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_plans = []

    existing = False
    for i, plan in enumerate(all_plans):
        if plan["week_number"] == week_number:
            all_plans[i] = week_record
            existing = True
            break

    if not existing:
        all_plans.append(week_record)

    with open(filename, "w") as f:
        json.dump(all_plans, f, indent=2)

    print(f"  Saved to {filename}!")