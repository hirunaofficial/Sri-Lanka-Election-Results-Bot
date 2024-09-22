import telebot
import json
from telebot import types

# Replace with your bot's token
TOKEN = 'your_telegram_bot_token'

bot = telebot.TeleBot(TOKEN)

SUBSCRIPTION_FILE = 'subscriptions.json'

district_results = {
    "colombo": "Colombo Results: Party A - 40%, Party B - 35%, Party C - 25%",
    "gampaha": "Gampaha Results: Party A - 42%, Party B - 33%, Party C - 25%"
}

overall_results = "Overall Results: Party A - 45 seats, Party B - 40 seats, Party C - 15 seats"

def load_subscriptions():
    try:
        with open(SUBSCRIPTION_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}

def save_subscriptions(subscriptions):
    with open(SUBSCRIPTION_FILE, 'w') as file:
        json.dump(subscriptions, file)

user_subscriptions = load_subscriptions()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to the Sri Lanka Election Results Bot 🇱🇰. Use /district, /overall, /subscribe, /unsubscribe commands.")

@bot.message_handler(commands=['district'])
def send_district_result(message):
    try:
        district_name = message.text.split()[1].lower()
        if district_name in district_results:
            bot.reply_to(message, district_results[district_name])
        else:
            bot.reply_to(message, "Sorry, I don't have results for that district.")
    except IndexError:
        bot.reply_to(message, "Please provide a district name. Example: /district colombo")

@bot.message_handler(commands=['overall'])
def send_overall_result(message):
    bot.reply_to(message, overall_results)

@bot.message_handler(commands=['subscribe'])
def subscribe_to_updates(message):
    try:
        user_id = str(message.from_user.id)
        district_name = message.text.split()[1].lower()
        
        if district_name in district_results:
            user_subscriptions[user_id] = district_name
            save_subscriptions(user_subscriptions)  # Save subscription to JSON
            bot.reply_to(message, f"You have subscribed to updates for {district_name}.")
        else:
            bot.reply_to(message, "Sorry, I don't have results for that district.")
    except IndexError:
        bot.reply_to(message, "Please provide a district name. Example: /subscribe colombo")

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe_from_updates(message):
    user_id = str(message.from_user.id)
    if user_id in user_subscriptions:
        del user_subscriptions[user_id]
        save_subscriptions(user_subscriptions)  # Save updated subscriptions to JSON
        bot.reply_to(message, "You have been unsubscribed from updates.")
    else:
        bot.reply_to(message, "You are not subscribed to any updates.")

def send_updates(district_name, new_results):
    global district_results
    district_results[district_name] = new_results

    for user_id, subscribed_district in user_subscriptions.items():
        if subscribed_district == district_name:
            bot.send_message(user_id, f"New update for {district_name}: {new_results}")

bot.polling()
