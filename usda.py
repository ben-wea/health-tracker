import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("USDA_API_KEY")
SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# USDA nutrient numbers are stable identifiers; names vary between entries.
NUTRIENT_NUMBERS = {
    "203": "protein",
    "205": "carbs",
    "204": "fat",
}


class USDAError(Exception):
    """Raised when the USDA API cannot be reached or returns bad data."""


KJ_PER_KCAL = 4.184

# Energy is reported under different nutrient numbers depending on the dataset.
# Preference order: measured kcal, Atwater specific, Atwater general, kJ.
ENERGY_NUMBERS = ["208", "958", "957"]


def _extract_nutrients(food):
    """Pull the four nutrients we care about out of a USDA food object.

    Foundation foods report energy as Atwater factors (957/958) rather than
    nutrient 208, and some entries give only kilojoules (268).
    """
    nutrients = {"calories": 0.0, "protein": 0.0, "carbs": 0.0, "fat": 0.0}
    energy = {}

    for item in food.get("foodNutrients", []):
        number = str(item.get("nutrientNumber", ""))
        value = float(item.get("value") or 0.0)

        if number in NUTRIENT_NUMBERS:
            nutrients[NUTRIENT_NUMBERS[number]] = value
        elif number in ENERGY_NUMBERS or number == "268":
            energy[number] = value

    for number in ENERGY_NUMBERS:
        if energy.get(number):
            nutrients["calories"] = energy[number]
            break
    else:
        if energy.get("268"):
            nutrients["calories"] = round(energy["268"] / KJ_PER_KCAL, 1)

    return nutrients


def search_foods(query, page_size=10):
    """Search USDA FoodData Central and return simplified food dicts.

    Each result has: fdc_id, description, and per-100g nutrition values.
    """
    if not API_KEY:
        raise USDAError("USDA_API_KEY is not set. Check your .env file.")

    params = {
        "query": query,
        "pageSize": page_size,
        "dataType": "Foundation, SR Legacy",
        "api_key": API_KEY,
    }

    try:
        response = requests.get(SEARCH_URL, params=params, timeout=10)
    except requests.exceptions.Timeout:
        raise USDAError("The USDA API took too long to respond.")
    except requests.exceptions.RequestException as exc:
        raise USDAError(f"Could not reach the USDA API: {exc}")

    if response.status_code == 403:
        raise USDAError("USDA rejected the API key (403). Check your .env file.")
    if response.status_code == 429:
        raise USDAError("Rate limit reached. Wait a moment and try again.")
    if response.status_code != 200:
        raise USDAError(f"USDA API returned status {response.status_code}.")

    try:
        payload = response.json()
    except ValueError:
        raise USDAError("USDA returned a response that was not valid JSON.")

    results = []
    for food in payload.get("foods", []):
        nutrients = _extract_nutrients(food)
        results.append({
            "fdc_id": food.get("fdcId"),
            "description": food.get("description", "Unknown food"),
            "calories_per_100g": nutrients["calories"],
            "protein_per_100g": nutrients["protein"],
            "carbs_per_100g": nutrients["carbs"],
            "fat_per_100g": nutrients["fat"],
        })

    return results