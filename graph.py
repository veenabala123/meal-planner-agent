from langgraph.graph import StateGraph, START, END
from state import MealPlannerState
from nodes import generate_meals, check_rotation, validate_balance, swap_meal


def should_retry(state):
    """Conditional edge: decide what happens after rotation check."""

    # If rotation failed and we haven't retried too many times, try again
    if not state["rotation_valid"] and state["retry_count"] < 3:
        print(f"  Retrying... (attempt {state['retry_count'] + 1} of 3)")
        return "retry"

    # If we've retried 3 times, give up and accept what we have
    if state["retry_count"] >= 3:
        print("  Max retries reached — accepting current plan")
        return "accept"

    # Rotation passed — move forward
    return "accept"

def should_swap_again(state):
    """Conditional edge: did the human request another swap?"""
    if state.get("swap_requested", False):
        return "swap_again"
    return "done"


# === BUILD THE GRAPH ===

# Step 1: Create the graph with our state type
graph = StateGraph(MealPlannerState)

# Step 2: Add nodes (each is a Python function)
graph.add_node("generate_meals", generate_meals)
graph.add_node("check_rotation", check_rotation)
graph.add_node("validate_balance", validate_balance)
graph.add_node("swap_meal", swap_meal)

# Step 3: Add edges (the wiring!)
graph.add_edge(START, "generate_meals")          # Start → generate
graph.add_edge("generate_meals", "check_rotation")  # generate → check

# Step 4: Add the CONDITIONAL edge (this is the magic)
graph.add_conditional_edges(
    "check_rotation",       # After this node...
    should_retry,           # ...run this function to decide...
    {
        "retry": "generate_meals",    # if "retry" → go back
        "accept": "validate_balance"  # if "accept" → move forward
    }
)

graph.add_edge("validate_balance", "swap_meal")  # validate → done!

graph.add_conditional_edges(
    "swap_meal",
    should_swap_again,
    {"swap_again": "swap_meal", "done": END}
)

# Step 5: Compile the graph (makes it runnable)
app = graph.compile()

print("Graph compiled successfully!")
