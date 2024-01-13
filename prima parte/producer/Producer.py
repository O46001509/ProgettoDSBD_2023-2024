import logging, os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from infoWeather import *

# Leggi il token dal file
#with open("tokenBot.txt", 'r') as tkn:
#    TOKEN = tkn.read()

# Leggi il token dal file specificato dalla variabile di ambiente se è presente
telegram_token_file = os.environ.get("TELEGRAM_TOKEN_FILE", "tokenBot.txt")
with open(telegram_token_file, 'r') as tkn:
    TELEGRAM_TOKEN = tkn.read()

# Configura il logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

user_states = {}

# Handler per il comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = 'awaiting_name'
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, insert your name!")

# Handler per gestire i messaggi di testo
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if user_id in user_states:
        if user_states[user_id] == 'awaiting_name':
            # Salvo il nome nell'oggetto context.user_data e chiedo la città
            context.user_data['user_name'] = user_message
            user_states[user_id] = 'awaiting_city'
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Hello {user_message}, now please enter your city!")

        elif user_states[user_id] == 'awaiting_city':
            # Recupero il nome salvato e procedo
            user_name = context.user_data.get('user_name', 'Unknown User')
            user_city = user_message
            del user_states[user_id]  # Rimuove lo stato dell'utente se la conversazione è finita

            publish_on_topic(user_name, user_city)

            info_weather = return_weather(user_city)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{info_weather}")
        else:
            # Se non ci sono altri stati definiti
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Please use the /start command to begin.")
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Please use the /start command to begin.")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Aggiungi gli handler
    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)

    application.add_handler(start_handler)
    application.add_handler(message_handler)

    # Avvia il bot
    application.run_polling()



