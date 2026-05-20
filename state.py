
from typing import TypedDict, Annotated
from operator import add

class MealPlannerState(TypedDict):
    proteins: list[str]
    restrictions: list[str]
    cuisines: list[str]
    spice_level: str

    week_number: int
    current_meals: list[dict]

    previous_weeks: list[list[dict]]

    rotation_valid: bool
    balance_valid: bool 
    retry_count: int
    swap_requested: bool
    
