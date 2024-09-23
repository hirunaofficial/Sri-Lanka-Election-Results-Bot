import telebot
import json
import requests
import time
import threading
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
AUTH_TOKEN = os.getenv('AUTHORIZATION_TOKEN')

bot = telebot.TeleBot(TOKEN)
USER_DATA_FILE = 'users.json'
BASE_API_URL = "http://127.0.0.1:5000/api"
AUTH_HEADER = {
    "Authorization": AUTH_TOKEN
}

ADMIN_ID = 1108072683  # Admin's Telegram ID
election_active = True  # Global flag to track if the election is active

def load_user_data():
    try:
        with open(USER_DATA_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w') as file:
        json.dump(data, file)

user_data = load_user_data()
last_sent_message = ""

def is_election_active(func):
    def wrapper(message):
        user_id = str(message.from_user.id)
        if user_id not in user_data:
            user_data[user_id] = {"subscribed": True}
            save_user_data(user_data)

        if not election_active:
            bot.reply_to(message, "🚨 The election has ended. Thank you for staying informed! 🙏")
        else:
            return func(message)
    return wrapper

@bot.message_handler(commands=['start'])
@is_election_active
def send_welcome(message):
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        user_data[user_id] = {"subscribed": True}
        save_user_data(user_data)
        bot.reply_to(message, "👋 Welcome to the Sri Lanka Election Results Bot 🇱🇰!\n\nYou have been automatically subscribed to receive the latest election results. 📰\n\nUse /help to see available commands.", parse_mode='Markdown')
    else:
        bot.reply_to(message, "👋 Welcome back to the Sri Lanka Election Results Bot 🇱🇰!\n\nUse /help to see available commands.", parse_mode='Markdown')

@bot.message_handler(commands=['help'])
@is_election_active
def send_help(message):
    help_text = (
        "🛠️ Here are the commands you can use:\n\n"
        "📊 `/results` - Check the overall election results.\n"
        "📍 `/district [district]` - Get detailed results for a specific district.\n"
        "🏘️ `/division [district] [division]` - Get results for a specific division within a district.\n"
        "🔔 `/subscribe` - Subscribe to receive the latest election updates.\n"
        "🚫 `/unsubscribe` - Unsubscribe from overall updates.\n\n"
        "Stay informed with the latest election results! 🗳️"
    )
    bot.reply_to(message, help_text, parse_mode='Markdown')

@bot.message_handler(commands=['results'])
@is_election_active
def send_overall_result(message):
    try:
        response = requests.get(f"{BASE_API_URL}/overall", headers=AUTH_HEADER)
        if response.status_code == 200:
            data = response.json().get('data', {})
            message_text = format_results(data)
            bot.reply_to(message, message_text, parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ Sorry, I couldn't fetch the overall results.")
    except Exception as e:
        bot.reply_to(message, f"🚨 An error occurred: {str(e)}")

@bot.message_handler(commands=['district'])
@is_election_active
def send_detailed_district_results(message):
    try:
        district_name = message.text.split()[1].capitalize()
        response = requests.get(f"{BASE_API_URL}/district?district={district_name}", headers=AUTH_HEADER)
        if response.status_code == 200:
            data = response.json().get('data', {})
            message_text = format_results(data)
            bot.reply_to(message, f"📍 Detailed Results for {district_name}:\n\n{message_text}", parse_mode='Markdown')
        else:
            bot.reply_to(message, "❌ Sorry, I couldn't fetch the results for that district.")
    except IndexError:
        bot.reply_to(message, "⚠️ Please provide a district name. Example: `/district Colombo`", parse_mode='Markdown')

@bot.message_handler(commands=['division'])
@is_election_active
def send_division_results(message):
    try:
        parts = message.text.split()
        district_name = parts[1].capitalize()
        division_name = parts[2].capitalize()
        response = requests.get(f"{BASE_API_URL}/division?district={district_name}&division={division_name}", headers=AUTH_HEADER)
        if response.status_code == 200:
            data = response.json().get('data', {})
            message_text = format_results(data)
            bot.reply_to(message, f"🏘️ Division Results for {division_name}, {district_name}:\n\n{message_text}", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"❌ Sorry, I couldn't fetch the results for the division {division_name} in {district_name}.")
    except IndexError:
        bot.reply_to(message, "⚠️ Please provide both a district and division. Example: `/division Colombo Medawachchiya`", parse_mode='Markdown')

@bot.message_handler(commands=['subscribe'])
@is_election_active
def subscribe_to_updates(message):
    user_id = str(message.from_user.id)
    if user_id in user_data:
        user_data[user_id]["subscribed"] = True
        save_user_data(user_data)
        bot.reply_to(message, "✅ You have successfully subscribed to the latest election updates!", parse_mode='Markdown')
    else:
        bot.reply_to(message, "⚠️ Please start the bot first using /start.")

@bot.message_handler(commands=['unsubscribe'])
@is_election_active
def unsubscribe_from_updates(message):
    user_id = str(message.from_user.id)
    if user_id in user_data and user_data[user_id]["subscribed"]:
        user_data[user_id]["subscribed"] = False
        save_user_data(user_data)
        bot.reply_to(message, "🚫 You have successfully unsubscribed from overall election updates.", parse_mode='Markdown')
    else:
        bot.reply_to(message, "⚠️ You are not subscribed to the latest updates.")

@bot.message_handler(commands=['disable'])
def disable_election(message):
    global election_active
    if message.from_user.id == ADMIN_ID:
        election_active = False
        bot.reply_to(message, "🛑 The election is now over. All commands are disabled. Thank you for using the bot!")
    else:
        bot.reply_to(message, "⚠️ You do not have permission to disable the bot.")

@bot.message_handler(commands=['enable'])
def enable_election(message):
    global election_active
    if message.from_user.id == ADMIN_ID:
        election_active = True
        bot.reply_to(message, "✅ The bot is now enabled. You can use all commands again.")
    else:
        bot.reply_to(message, "⚠️ You do not have permission to enable the bot.")

def format_results(data):
    # (Same format_results function as before)
    pass

# Start the polling
bot.polling()