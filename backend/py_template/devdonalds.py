from dataclasses import dataclass
from typing import List, Dict, Union
from flask import Flask, request, jsonify
import re

# ==== Type Definitions, feel free to add or modify ===========================
@dataclass
class CookbookEntry:
	name: str

@dataclass
class RequiredItem():
	name: str
	quantity: int

@dataclass
class Recipe(CookbookEntry):
	required_items: List[RequiredItem]

@dataclass
class Ingredient(CookbookEntry):
	cook_time: int


# =============================================================================
# ==== HTTP Endpoint Stubs ====================================================
# =============================================================================
app = Flask(__name__)

# Store your recipes here!
cookbook: Dict[str, Union["Recipe", "Ingredient"]] = {}

# Task 1 helper (don't touch)
@app.route("/parse", methods=['POST'])
def parse():
	data = request.get_json()
	recipe_name = data.get('input', '')
	parsed_name = parse_handwriting(recipe_name)
	if parsed_name is None:
		return 'Invalid recipe name', 400
	return jsonify({'msg': parsed_name}), 200

# [TASK 1] ====================================================================
# Takes in a recipeName and returns it in a form that 
def parse_handwriting(recipeName: str) -> Union[str | None]:
	if not isinstance(recipeName, str):
		return None

	# Replace separators with spaces, remove non-letters, and normalize spacing.
	normalized = re.sub(r"[-_]", " ", recipeName)
	normalized = re.sub(r"[^A-Za-z\s]", "", normalized)
	normalized = re.sub(r"\s+", " ", normalized).strip()

	if len(normalized) == 0:
		return None

	return " ".join(word.capitalize() for word in normalized.split(" "))


# [TASK 2] ====================================================================
# Endpoint that adds a CookbookEntry to your magical cookbook
@app.route('/entry', methods=['POST'])
def create_entry():
	data = request.get_json(silent=True)
	if not isinstance(data, dict):
		return 'invalid entry', 400

	entry_type = data.get("type")
	name = data.get("name")

	if entry_type not in {"recipe", "ingredient"} or not isinstance(name, str):
		return 'invalid entry', 400

	if name in cookbook:
		return 'duplicate name', 400

	if entry_type == "ingredient":
		cook_time = data.get("cookTime")
		if not isinstance(cook_time, int) or cook_time < 0:
			return 'invalid ingredient', 400
		cookbook[name] = Ingredient(name=name, cook_time=cook_time)
		return jsonify({}), 200

	required_items_raw = data.get("requiredItems")
	if not isinstance(required_items_raw, list):
		return 'invalid recipe', 400

	seen_required_names = set()
	required_items: List[RequiredItem] = []

	for item in required_items_raw:
		if not isinstance(item, dict):
			return 'invalid recipe', 400
		item_name = item.get("name")
		quantity = item.get("quantity")
		if not isinstance(item_name, str) or not isinstance(quantity, int):
			return 'invalid recipe', 400
		if item_name in seen_required_names:
			return 'invalid recipe', 400
		seen_required_names.add(item_name)
		required_items.append(RequiredItem(name=item_name, quantity=quantity))

	cookbook[name] = Recipe(name=name, required_items=required_items)
	return jsonify({}), 200


# [TASK 3] ====================================================================
# Endpoint that returns a summary of a recipe that corresponds to a query name
@app.route('/summary', methods=['GET'])
def summary():
	name = request.args.get("name")
	if not isinstance(name, str) or name not in cookbook:
		return 'recipe not found', 400

	root = cookbook[name]
	if not isinstance(root, Recipe):
		return 'not a recipe', 400

	ingredient_totals: Dict[str, int] = {}
	total_cook_time = 0

	def resolve(entry_name: str, multiplier: int, visiting: set[str]) -> bool:
		nonlocal total_cook_time

		entry = cookbook.get(entry_name)
		if entry is None:
			return False

		if isinstance(entry, Ingredient):
			ingredient_totals[entry.name] = ingredient_totals.get(entry.name, 0) + multiplier
			total_cook_time += entry.cook_time * multiplier
			return True

		# Prevent infinite recursion for cyclic recipe graphs.
		if entry_name in visiting:
			return False

		next_visiting = set(visiting)
		next_visiting.add(entry_name)

		for item in entry.required_items:
			if not resolve(item.name, multiplier * item.quantity, next_visiting):
				return False
		return True

	if not resolve(name, 1, set()):
		return 'invalid recipe graph', 400

	ingredients_list = [
		{"name": ingredient_name, "quantity": quantity}
		for ingredient_name, quantity in ingredient_totals.items()
	]

	return jsonify({
		"name": name,
		"cookTime": total_cook_time,
		"ingredients": ingredients_list,
	}), 200


# =============================================================================
# ==== DO NOT TOUCH ===========================================================
# =============================================================================

if __name__ == '__main__':
	app.run(debug=True, port=8080)
