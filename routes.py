from flask import Blueprint, render_template, request, redirect, url_for

main = Blueprint('main', __name__)

# Dummy data (je kunt dit later koppelen aan een echte DB)
bikes = [
    {"id": 1, "name": "Gazelle CityGo", "type": "Stadsfiets", "status": "Beschikbaar"},
    {"id": 2, "name": "Cortina E-U4", "type": "Elektrische fiets", "status": "Verhuurd"},
    {"id": 3, "name": "Batavus Quip", "type": "Stadsfiets", "status": "Beschikbaar"}
]

@main.route('/')
def home():
    return render_template('index.html')

@main.route('/bikes')
def bike_list():
    return render_template('bikes.html', bikes=bikes)

@main.route('/rent/<int:bike_id>')
def rent_bike(bike_id):
    bike = next((b for b in bikes if b["id"] == bike_id), None)
    return render_template('rent.html', bike=bike)

@main.route('/about')
def about():
    return render_template('about.html')

