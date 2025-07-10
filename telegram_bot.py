import json
import folium
from geopy.geocoders import Nominatim
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Path to the JSON file and the map file
DATA_FILE = 'risk_data.json'
MAP_FILE = 'map.html'

# Initialize geocoder (Nominatim API)
geolocator = Nominatim(user_agent="health_risk_bot")

# Load existing data or initialize an empty dictionary
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save updated data to JSON file
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Initialize risk data
risk_data = load_data()

# Get coordinates dynamically using Nominatim
def get_coordinates(location_name):
    try:
        location = geolocator.geocode(location_name, timeout=5)
        if location:
            return [location.latitude, location.longitude]
        else:
            return None
    except Exception as e:
        print(f"Error getting coordinates for {location_name}: {e}")
        return None

# Generate a folium map based on the risk data
def generate_map(risk_data):
    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5)

    # Define color codes for different risk levels
    risk_colors = {
        'Low Risk': 'green',
        'Moderate Risk': 'orange',
        'High Risk': 'red'
    }

    for state, data in risk_data.items():
        coords = get_coordinates(state)
        if coords:
            risk_level = data.get('Risk_level', 'Unknown')
            color = risk_colors.get(risk_level, 'blue')

            popup_html = f"""
            <b>{state}</b><br>
            Risk Level: {risk_level}<br>
            Cancer Percentage: {data.get('Cancer Percentage', 'N/A')}<br>
            Chronic Illness Percentage: {data.get('Chronic Illness Percentage', 'N/A')}<br>
            Mortality Rate: {data.get('Mortality Rate', 'N/A')}<br>
            Number of Hospitals: {data.get('Number of Hospitals', 'N/A')}<br>
            Cancer Care Centers: {data.get('Cancer Care Centers', 'N/A')}<br>
            Health Insurance Coverage: {data.get('Health Insurance Coverage', 'N/A')}
            """

            folium.Marker(
                location=coords,
                popup=folium.Popup(popup_html, max_width=500),
                icon=folium.Icon(color=color),
                tooltip=state
            ).add_to(m)

    # Save the map to an HTML file
    m.save(MAP_FILE)

# Command handlers for the Telegram bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Welcome to the Health Risk Bot.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(""" 
    The following commands are available:
    
    /start -> Welcome message
    /help -> This message
    /add_city <city/state> -> Add a city or state with coordinates
    /update <state> <parameter> <value> -> Update a specific parameter for a state
    /show <state> -> Show current risk data for a particular state
    /remove <city/state> -> Remove a city/state from the map
    /map -> Show the current risk map
    """)

# Default parameters template for a new city/state (CLEANED)
DEFAULT_PARAMETERS = {
    "Risk_level": "No data yet",
    "Cancer Percentage": "N/A",
    "Chronic Illness Percentage": "N/A",
    "Mortality Rate": "N/A",
    "Number of Hospitals": "N/A",
    "Cancer Care Centers": "N/A",
    "Health Insurance Coverage": "N/A"
}

# Add a city/state and its coordinates based on the name
async def add_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /add_city <city/state>")
        return

    city_name = ' '.join(context.args)

    if city_name in risk_data:
        await update.message.reply_text(f"{city_name} is already in the system.")
        return

    coords = get_coordinates(city_name)
    if not coords:
        await update.message.reply_text(f"Could not find coordinates for {city_name}.")
        return

    risk_data[city_name] = {
        "coordinates": coords,
        **DEFAULT_PARAMETERS
    }

    save_data(risk_data)
    generate_map(risk_data)

    await update.message.reply_text(f"{city_name} has been added with coordinates: {coords}.")

# Update the risk data for a specific state and parameter
async def update_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /update <state> <parameter> <value>")
        return

    state = context.args[0]
    parameter = context.args[1]
    value = ' '.join(context.args[2:])

    if state not in risk_data:
        await update.message.reply_text(f"No data for {state}. Use /add_city to add it first.")
        return

    parameter_key = parameter.lower().replace(" ", "_")

    found = False
    for key in risk_data[state]:
        normalized_key = key.lower().replace(" ", "_")
        if normalized_key == parameter_key:
            risk_data[state][key] = value
            found = True
            break

    if found:
        save_data(risk_data)
        generate_map(risk_data)
        await update.message.reply_text(f"{parameter} for {state} updated to '{value}'.")
    else:
        await update.message.reply_text(f"Parameter '{parameter}' not found for {state}.")

# Show the current risk data for a particular state
async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /show <state>")
        return

    state = context.args[0]
    if state not in risk_data:
        await update.message.reply_text(f"No data available for {state}.")
    else:
        data = risk_data[state]
        response = f"""
        {state} Risk Data:
        Risk Level: {data.get('Risk_level', 'N/A')}
        Cancer Percentage: {data.get('Cancer Percentage', 'N/A')}
        Chronic Illness Percentage: {data.get('Chronic Illness Percentage', 'N/A')}
        Mortality Rate: {data.get('Mortality Rate', 'N/A')}
        Number of Hospitals: {data.get('Number of Hospitals', 'N/A')}
        Cancer Care Centers: {data.get('Cancer Care Centers', 'N/A')}
        Health Insurance Coverage: {data.get('Health Insurance Coverage', 'N/A')}
        """
        await update.message.reply_text(response)

# Remove a city/state from the risk data
async def remove_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /remove <city/state>")
        return

    city_name = ' '.join(context.args)

    if city_name not in risk_data:
        await update.message.reply_text(f"{city_name} is not in the system.")
    else:
        del risk_data[city_name]
        save_data(risk_data)
        generate_map(risk_data)
        await update.message.reply_text(f"{city_name} has been removed from the map and data.")

# Show the current map
async def show_map(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(MAP_FILE, 'rb') as f:
            await update.message.reply_document(f)
    except FileNotFoundError:
        await update.message.reply_text("No map available. Please update the data first.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"You said: {update.message.text}. Use the commands with /")

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
Token = "8025890764:AAFVUQt-jMKMa2pednocKjAqzghmvm-huO8"

# Initialize the application and add handlers
application = ApplicationBuilder().token(Token).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("add_city", add_city))
application.add_handler(CommandHandler("update", update_data))
application.add_handler(CommandHandler("show", show_data))
application.add_handler(CommandHandler("remove", remove_city))
application.add_handler(CommandHandler("map", show_map))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Run the bot
application.run_polling()
