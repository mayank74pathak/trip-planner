
from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "Trip Planner MCP Server",
    host="0.0.0.0",
    port=8001,
)


@mcp.tool()
def estimate_trip_cost(
    nights: int,
    travelers: int,
    accommodation_per_night: float,
    food_per_person_per_day: float,
    transport_total: float,
    activities_per_person: float,
    budget: float,
) -> dict:
    """Estimate trip expenses and check whether they fit the budget.

    All monetary amounts are in INR.
    Food is calculated for nights + 1 days.
    Activities are calculated per traveler for the whole trip.
    """

    if nights < 1:
        raise ValueError("Nights must be at least 1.")

    if travelers < 1:
        raise ValueError("Travelers must be at least 1.")

    amounts = [
        accommodation_per_night,
        food_per_person_per_day,
        transport_total,
        activities_per_person,
        budget,
    ]

    if any(amount < 0 for amount in amounts):
        raise ValueError("Costs and budget cannot be negative.")

    accommodation = nights * accommodation_per_night
    food = (nights + 1) * travelers * food_per_person_per_day
    activities = travelers * activities_per_person

    total = accommodation + food + transport_total + activities

    return {
        "currency": "INR",
        "accommodation": round(accommodation, 2),
        "food": round(food, 2),
        "transport": round(transport_total, 2),
        "activities": round(activities, 2),
        "estimated_total": round(total, 2),
        "budget": round(budget, 2),
        "remaining_budget": round(budget - total, 2),
        "within_budget": total <= budget,
    }


@mcp.tool()
def search_attractions(destination: str) -> dict:
    """Find sample attractions for a supported destination.

    This initial version uses a local sample dataset,
    not live internet search.
    """

    attractions = {
        "goa": [
            {"name": "Baga Beach", "category": "Beach"},
            {"name": "Fort Aguada", "category": "History"},
            {"name": "Dudhsagar Falls", "category": "Nature"},
            {"name": "Fontainhas", "category": "Culture"},
        ],
        "jaipur": [
            {"name": "Amber Fort", "category": "History"},
            {"name": "Hawa Mahal", "category": "Architecture"},
            {"name": "City Palace", "category": "Culture"},
        ],
        "delhi": [
            {"name": "Red Fort", "category": "History"},
            {"name": "India Gate", "category": "Landmark"},
            {"name": "Humayun's Tomb", "category": "Architecture"},
        ],
    }

    key = destination.strip().lower()
    results = attractions.get(key, [])

    return {
        "destination": destination,
        "source": "local sample dataset",
        "count": len(results),
        "attractions": results,
        "message": (
            "Sample attractions returned."
            if results
            else "No sample attractions available for this destination."
        ),
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
