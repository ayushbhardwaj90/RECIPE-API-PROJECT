import json
import re

from app import Recipe, app, db


def robust_clean_numeric(value):
    """
    A more robust function to clean and convert a value to a float.
    Handles numbers, strings with numbers, 'NaN', None, and other edge cases.
    """
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        if value.lower() == 'nan':
            return None
        
        match = re.search(r'(\d+\.?\d*|\.\d+)', value)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, TypeError):
                return None

    return None

def setup_database():
    """
    Drops, creates, and populates the database from the JSON file.
    """
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()

        print("Loading data from US_Recipes_null.json...")
        with open('US_Recipes_null.json', 'r', encoding='utf-8') as f:
            recipes_data = json.load(f)

        recipes_to_add = []
        skipped_count = 0
        
        for recipe_data in recipes_data.values():
            # FINAL FIX: Check if a title exists. If not, skip this recipe.
            if not recipe_data.get('title'):
                skipped_count += 1
                continue # Go to the next recipe in the loop

            cleaned_nutrients = {}
            if 'nutrients' in recipe_data and isinstance(recipe_data['nutrients'], dict):
                for key, val in recipe_data['nutrients'].items():
                    cleaned_nutrients[key] = robust_clean_numeric(val)
            
            new_recipe = Recipe(
                cuisine=recipe_data.get('cuisine'),
                title=recipe_data.get('title'),
                rating=robust_clean_numeric(recipe_data.get('rating')),
                prep_time=robust_clean_numeric(recipe_data.get('prep_time')),
                cook_time=robust_clean_numeric(recipe_data.get('cook_time')),
                total_time=robust_clean_numeric(recipe_data.get('total_time')),
                description=recipe_data.get('description'),
                serves=recipe_data.get('serves'),
                nutrients=cleaned_nutrients
            )
            recipes_to_add.append(new_recipe)

        print(f"Adding {len(recipes_to_add)} recipes to the database...")
        print(f"Skipped {skipped_count} recipes due to missing titles.")
        db.session.bulk_save_objects(recipes_to_add)
        db.session.commit()
        print("Database setup complete!")

if __name__ == '__main__':
    setup_database()