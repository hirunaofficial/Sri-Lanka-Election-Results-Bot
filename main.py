import telebot
import json
import requests
import time
import threading
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

bot = telebot.TeleBot(TOKEN)
USER_DATA_FILE = 'users.json'
API_URL = "https://example.com/election/results"

district_results = {
    "colombo": "Colombo Results: Party A - 40%, Party B - 35%, Party C - 25%",
    "gampaha": "Gampaha Results: Party A - 42%, Party B - 33%, Party C - 25%"
}

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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        user_data[user_id] = {"subscribed": True}
        save_user_data(user_data)
    bot.reply_to(message, "👋 Welcome to the Sri Lanka Election Results Bot 🇱🇰!\nUse /help to see available commands.")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "🛠️ Here are the commands you can use:\n"
        "/results [district] - Check election results for a specific district.\n"
        "/subscribe - Subscribe to receive overall election updates.\n"
        "/unsubscribe - Unsubscribe from overall updates.\n"
        "🔔 Stay informed with the latest election results!"
    )
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['results'])
def send_district_result(message):
    try:
        district_name = message.text.split()[1].lower()
        if district_name in district_results:
            bot.reply_to(message, district_results[district_name])
        else:
            bot.reply_to(message, "❌ Sorry, I don't have results for that district.")
    except IndexError:
        bot.reply_to(message, "⚠️ Please provide a district name. Example: /results colombo")

@bot.message_handler(commands=['subscribe'])
def subscribe_to_updates(message):
    user_id = str(message.from_user.id)
    if user_id in user_data:
        user_data[user_id]["subscribed"] = True
        save_user_data(user_data)
        bot.reply_to(message, "✅ You have subscribed to overall updates.")
    else:
        bot.reply_to(message, "⚠️ Please start the bot first using /start.")

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_from_updates(message):
    user_id = str(message.from_user.id)
    if user_id in user_data and user_data[user_id]["subscribed"]:
        user_data[user_id]["subscribed"] = False
        save_user_data(user_data)
        bot.reply_to(message, "🚫 You have unsubscribed from overall updates.")
    else:
        bot.reply_to(message, "⚠️ You are not subscribed to overall updates.")

def fetch_overall_results():
    response = requests.get(API_URL)
    if response.status_code == 200:
        return response.json().get('overall_results', 'No overall results available.')
    else:
        return "🚨 Error fetching overall results."

def send_overall_updates():
    overall_results = fetch_overall_results()
    for user_id, user_info in user_data.items():
        if user_info["subscribed"]:
            bot.send_message(user_id, f"🔄 Overall Update: {overall_results}")

def schedule_updates(interval):
    while True:
        send_overall_updates()
        time.sleep(interval)

bot.polling()

update_thread = threading.Thread(target=schedule_updates, args=(1,))
update_thread.start()