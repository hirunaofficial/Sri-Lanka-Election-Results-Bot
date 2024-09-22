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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    if user_id not in user_data:
        user_data[user_id] = {"subscribed": True}
        save_user_data(user_data)
        bot.reply_to(message, "👋 Welcome to the Sri Lanka Election Results Bot 🇱🇰!\n\nYou have been automatically subscribed to receive the latest election results. 📰\n\nUse /help to see available commands.", parse_mode='Markdown')
    else:
        bot.reply_to(message, "👋 Welcome back to the Sri Lanka Election Results Bot 🇱🇰!\n\nUse /help to see available commands.", parse_mode='Markdown')

@bot.message_handler(commands=['help'])
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
def subscribe_to_updates(message):
    user_id = str(message.from_user.id)
    if user_id in user_data:
        user_data[user_id]["subscribed"] = True
        save_user_data(user_data)
        bot.reply_to(message, "✅ You have successfully subscribed to the latest election updates!", parse_mode='Markdown')
    else:
        bot.reply_to(message, "⚠️ Please start the bot first using /start.")

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_from_updates(message):
    user_id = str(message.from_user.id)
    if user_id in user_data and user_data[user_id]["subscribed"]:
        user_data[user_id]["subscribed"] = False
        save_user_data(user_data)
        bot.reply_to(message, "🚫 You have successfully unsubscribed from overall election updates.", parse_mode='Markdown')
    else:
        bot.reply_to(message, "⚠️ You are not subscribed to the latest updates.")

def format_results(data):
    if 'results' not in data or len(data['results']) == 0:
        return "ℹ️ No results available."

    top_candidates = sorted(data['results'], key=lambda x: int(x['votes_received'].replace(',', '')), reverse=True)[:5]

    result_message = f"📊 {data.get('message', 'Results')}:\n\n"
    for result in top_candidates:
        result_message += (
            f"🗳️ {result['candidate_name']} ({result['party_abbreviation']}):\n"
            f"  • {result['percentage']} of the vote\n"
            f"  • {result['votes_received']} votes received\n\n"
        )
    result_message += "🔗 Source: [elections.gov.lk](https://www.elections.gov.lk)"
    return result_message

def fetch_latest_election_results():
    response = requests.get(f"{BASE_API_URL}/election", headers=AUTH_HEADER)
    if response.status_code == 200:
        data = response.json().get('data', {})
        return format_results(data)
    else:
        return "🚨 Error fetching the latest election results."

def send_latest_election_updates():
    global last_sent_message
    latest_results = fetch_latest_election_results()

    if latest_results != last_sent_message:
        for user_id, user_info in user_data.items():
            if user_info["subscribed"]:
                bot.send_message(user_id, f"🆕 New Election Results:\n\n{latest_results}", parse_mode='Markdown')
        last_sent_message = latest_results
    else:
        print("No new election results to send.")

def schedule_updates(interval):
    while True:
        send_latest_election_updates()
        time.sleep(interval)

# Start the update thread before polling
update_thread = threading.Thread(target=schedule_updates, args=(5,))
update_thread.start()

# Start polling for bot commands
bot.polling()