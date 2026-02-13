import os
import sqlite3
import requests
from flask import Flask, request, render_template_string
from dotenv import load_dotenv
from openai import OpenAI

# ===============================
# LOAD ENV VARIABLES
# ===============================
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

# ===============================
# DATABASE INITIALIZATION
# ===============================
def init_db():
    conn = sqlite3.connect("travel.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            destination TEXT,
            budget INTEGER,
            days INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ===============================
# AI ITINERARY GENERATOR
# ===============================
def generate_ai_itinerary(destination, budget, days):
    prompt = f"""
    Create a detailed {days}-day budget-friendly travel itinerary for a student visiting {destination}.
    Budget: ₹{budget}

    Include:
    - Affordable hostel/hotel suggestions
    - Cheap transport options
    - Student discounts
    - Daily plan
    - Estimated cost breakdown
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

# ===============================
# GOOGLE MAPS COORDINATES
# ===============================
def get_coordinates(place):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": place,
        "key": GOOGLE_MAPS_API_KEY
    }

    response = requests.get(url, params=params).json()

    if response["status"] == "OK":
        location = response["results"][0]["geometry"]["location"]
        return location["lat"], location["lng"]
    return None, None

# ===============================
# BUDGET CALCULATOR
# ===============================
def calculate_budget(total_budget):
    return {
        "Stay": round(total_budget * 0.4),
        "Food": round(total_budget * 0.25),
        "Transport": round(total_budget * 0.2),
        "Activities": round(total_budget * 0.15)
    }

# ===============================
# HOME PAGE
# ===============================
@app.route("/")
def home():
    return render_template_string("""
    <html>
    <head>
        <title>AI Travel Planner</title>
        <style>
            body { font-family: Arial; padding: 30px; background: #f2f2f2; }
            h1 { color: #2c3e50; }
            input, button { padding: 8px; margin: 5px; }
            button { background: #3498db; color: white; border: none; }
        </style>
    </head>
    <body>
        <h1>🎒 AI Travel Planner for Students</h1>
        <form action="/plan" method="post">
            Destination: <input type="text" name="destination" required><br>
            Budget (₹): <input type="number" name="budget" required><br>
            Days: <input type="number" name="days" required><br>
            <button type="submit">Generate Plan</button>
        </form>
    </body>
    </html>
    """)

# ===============================
# PLAN GENERATION
# ===============================
@app.route("/plan", methods=["POST"])
def plan():
    destination = request.form["destination"]
    budget = int(request.form["budget"])
    days = int(request.form["days"])

    # Save trip
    conn = sqlite3.connect("travel.db")
    c = conn.cursor()
    c.execute("INSERT INTO trips (destination, budget, days) VALUES (?, ?, ?)",
              (destination, budget, days))
    conn.commit()
    conn.close()

    # Generate AI itinerary
    itinerary = generate_ai_itinerary(destination, budget, days)

    # Budget breakdown
    budget_split = calculate_budget(budget)

    # Map coordinates
    lat, lng = get_coordinates(destination)

    return render_template_string("""
    <html>
    <head>
        <title>Your Travel Plan</title>
        <style>
            body { font-family: Arial; padding: 30px; background: #ffffff; }
            h2 { color: #2c3e50; }
            pre { background: #f4f4f4; padding: 15px; }
        </style>
    </head>
    <body>
        <h2>🌍 AI Generated Itinerary</h2>
        <pre>{{ itinerary }}</pre>

        <h3>💰 Budget Breakdown</h3>
        <ul>
            {% for key, value in budget_split.items() %}
                <li>{{ key }}: ₹{{ value }}</li>
            {% endfor %}
        </ul>

        <h3>📍 Location Map</h3>
        <iframe
            width="600"
            height="450"
            src="https://www.google.com/maps?q={{ lat }},{{ lng }}&output=embed">
        </iframe>

        <br><br>
        <a href="/">Plan Another Trip</a>
    </body>
    </html>
    """, itinerary=itinerary,
       budget_split=budget_split,
       lat=lat, lng=lng)

# ===============================
# RUN APP
# ===============================
if __name__ == "__main__":
    app.run(debug=True)