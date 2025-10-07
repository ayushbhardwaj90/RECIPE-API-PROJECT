import re

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.sql import func

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///recipes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


class Recipe(db.Model):
    """
    Represents a recipe in the database.
    """
    id = db.Column(db.Integer, primary_key=True)
    cuisine = db.Column(db.String(100), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    prep_time = db.Column(db.Integer, nullable=True)
    cook_time = db.Column(db.Integer, nullable=True)
    total_time = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    serves = db.Column(db.String(50), nullable=True)
    # Store nutrient information as a JSON object
    nutrients = db.Column(JSON, nullable=True)

    def to_dict(self):
        """
        Serializes the Recipe object to a dictionary.
        """
        return {
            "id": self.id,
            "title": self.title,
            "cuisine": self.cuisine,
            "rating": self.rating,
            "prep_time": self.prep_time,
            "cook_time": self.cook_time,
            "total_time": self.total_time,
            "description": self.description,
            "nutrients": self.nutrients,
            "serves": self.serves,
        }


def apply_numeric_filter(query, column, value_str):

    if not value_str:
        return query

    match = re.match(r"([<>]=?|=)(\d+\.?\d*)", value_str)
    if not match:
        try:
            value = float(value_str)
            return query.filter(column == value)
        except (ValueError, TypeError):
            return query
    
    op, val_str = match.groups()
    value = float(val_str)

    if op == '>=': return query.filter(column >= value)
    elif op == '<=': return query.filter(column <= value)
    elif op == '>': return query.filter(column > value)
    elif op == '<': return query.filter(column < value)
    elif op == '=': return query.filter(column == value)
    return query


@app.route('/api/recipes', methods=['GET'])
def get_all_recipes():
    """Endpoint to get all recipes, paginated and sorted by rating."""
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
    except ValueError:
        return jsonify({"error": "Invalid 'page' or 'limit'."}), 400

    pagination = Recipe.query.order_by(Recipe.rating.desc().nullslast()).paginate(page=page, per_page=limit, error_out=False)
    
    return jsonify({
        "page": pagination.page,
        "limit": pagination.per_page,
        "total": pagination.total,
        "data": [recipe.to_dict() for recipe in pagination.items]
    })


@app.route('/api/recipes/search', methods=['GET'])
def search_recipes():
    """Endpoint to search for recipes based on various filters."""
    query = Recipe.query

    if title := request.args.get('title'):
        query = query.filter(Recipe.title.ilike(f'%{title}%'))

    if cuisine := request.args.get('cuisine'):
        query = query.filter(func.lower(Recipe.cuisine) == func.lower(cuisine))
    
    if rating_filter := request.args.get('rating'):
        query = apply_numeric_filter(query, Recipe.rating, rating_filter)

    if total_time_filter := request.args.get('total_time'):
        query = apply_numeric_filter(query, Recipe.total_time, total_time_filter)

    if calories_filter := request.args.get('calories'):
        calories_column = func.json_extract(Recipe.nutrients, '$.calories').cast(db.Integer)
        query = apply_numeric_filter(query, calories_column, calories_filter)

    results = query.all()
    
    return jsonify({"data": [recipe.to_dict() for recipe in results]})

if __name__ == '__main__':
    app.run(debug=True)