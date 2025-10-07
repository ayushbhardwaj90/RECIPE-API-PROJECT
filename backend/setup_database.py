import json
import re

from app import Recipe, app, db


def clean_numeric_value(value):
    """
    Converts a value to a number if possible. Handles 'NaN'.
    Returns None if conversion is not possible.
    """
    if value is None or (isinstance(value, str) and value.lower() == 'nan'):
        return None
    
    if isinstance(value, (int, float)):
        return value

    if isinstance(value, str):
        match = re.search(r'\d+\.?\d*', value)
        if match:
            try:
                return float(match.group())
            except (ValueError, TypeError):
                return None
    return None

def setup_database():
    """
    Drops, creates, and populates the database from recipes.json.
    """
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()

        print("Loading data from recipes.json...")
        with open('recipes.json', 'r', encoding='utf-8') as f:
            recipes_data = json.load(f)

        recipes_to_add = []
        for recipe_data in recipes_data:
            cleaned_nutrients = {}
            if 'nutrients' in recipe_data and isinstance(recipe_data['nutrients'], dict):
                for key, val in recipe_data['nutrients'].items():
                    cleaned_nutrients[key] = clean_numeric_value(val)
            
            new_recipe = Recipe(
                cuisine=recipe_data.get('cuisine'),
                title=recipe_data.get('title'),
                rating=clean_numeric_value(recipe_data.get('rating')),
                prep_time=clean_numeric_value(recipe_data.get('prep_time')),
                cook_time=clean_numeric_value(recipe_data.get('cook_time')),
                total_time=clean_numeric_value(recipe_data.get('total_time')),
                description=recipe_data.get('description'),
                serves=recipe_data.get('serves'),
                nutrients=cleaned_nutrients
            )
            recipes_to_add.append(new_recipe)

        print(f"Adding {len(recipes_to_add)} recipes to the database...")
        db.session.bulk_save_objects(recipes_to_add)
        db.session.commit()
        print("Database setup complete!")

if __name__ == '__main__':
    setup_database()