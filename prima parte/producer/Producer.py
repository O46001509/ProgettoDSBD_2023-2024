import logging, os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from other_functions import *

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN_FILE", "NO_VARIABLE_FOUND")
# Basic logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

user_states = {}


# Handler per il comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Se lo stato dell'utente è già presente, ignoro il nuovo comando /start
    if user_id in user_states:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="You are already in a conversation. Please finish the current conversation before starting a new one.")
        return

    # Altrimenti, inizio una nuova conversazione
    user_states[user_id] = 'awaiting_name'
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, insert your name!")

# Handler per gestire i messaggi di testo
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if user_id in user_states:
        if user_states[user_id] == 'awaiting_name':
            # Salvo il nome nell'oggetto context.user_data e chiedo al'utente di inserire la città
            context.user_data['user_name'] = user_message
            user_states[user_id] = 'awaiting_city'
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Hello {user_message}, now please enter your city!")

        elif user_states[user_id] == 'awaiting_city':
            user_city = user_message

            info_weather = return_weather(user_city)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"{info_weather}")

            # Chiedo all'utente se vuole sottoscriversi all'evento meteo
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Do you want to subscribe to weather updates for {user_city}? (YES or NO)")

            user_states[user_id] = 'awaiting_subscription_response'
            context.user_data['user_city'] = user_city

        # Condizione per gestire la risposta alla sottoscrizione
        elif user_states[user_id] == 'awaiting_subscription_response':
            user_city = context.user_data.get('user_city')
            
            # Se l'utente risponde YES 
            if user_message.upper() == 'YES':
                
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Great! You are now subscribed to weather updates for {user_city}.")

                # Chiedo all'utente quali vincoli associati alla sottoscrizione vuole scegliere
                constraints_message = (
                    "Which of the following weather constraints do you want to choose for specific weather notifications?\n"
                    "1. Temperature\n"
                    "2. Perceived Temperature\n"
                    "3. Humidity\n"
                    "4. General Weather\n"
                    "5. Wind Speed\n"
                    "Please respond with the numbers of the constraints you want to choose (e.g., 2, 3)."
                )
                await context.bot.send_message(chat_id=update.effective_chat.id, text=constraints_message)

                # Aggiorno lo stato dell'utente per gestire la risposta ai vincoli
                user_states[user_id] = 'awaiting_constraints_response'
            elif user_message.upper() == 'NO':
                # Se l'utente risponde NO, non fa nessuna sottoscrizione
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Okay, you are not subscribed. If you change your mind, you can use /start again.")
                # Rimuovo lo stato dell'utente, così può ricominciare la conversazione
                del user_states[user_id]
            else:
                # L'utente ha inserito una risposta non valida
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid response. Please type YES or NO.")

        # Condizione per gestire la risposta ai vincoli
        elif user_states[user_id] == 'awaiting_constraints_response':
            user_constraints = user_message.split(',')

            valid_constraints = {'1', '2', '3', '4', '5'}

            # Verifica della forma coretta della risposta (numeri separati da virgola)
            if all(constraint.isdigit() and constraint in valid_constraints for constraint in user_constraints) and len(user_constraints) > 0:
                tmp_constraint = False
                feel_tmp_constraint = False
                hum_constraint = False
                weather_constraint = False
                wind_constraint = False

                # Imposto le variabili dei vincoli a True in base alle scelte dell'utente
                for constraint in user_constraints:
                    if constraint == '1':
                        tmp_constraint = True
                    elif constraint == '2':
                        feel_tmp_constraint = True
                    elif constraint == '3':
                        hum_constraint = True
                    elif constraint == '4':
                        weather_constraint = True
                    elif constraint == '5':
                        wind_constraint = True

                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Thanks! You have chosen the following constraints: {', '.join(user_constraints)}.")

                # Chiedo all'utente per quanto tempo desidera ricevere notifiche (in minuti)
                await context.bot.send_message(chat_id=update.effective_chat.id, text="For how long do you want to receive notifications for the subscribed event? Please enter a number in minutes.")

                # Aggiorno lo stato dell'utente per gestire la risposta alla durata delle notifiche
                user_states[user_id] = 'awaiting_duration_response'

                context.user_data['tmp_constraint'] = tmp_constraint
                context.user_data['feel_tmp_constraint'] = feel_tmp_constraint
                context.user_data['hum_constraint'] = hum_constraint
                context.user_data['weather_constraint'] = weather_constraint
                context.user_data['wind_constraint'] = wind_constraint
            else:
                # L'utente ha inserito una risposta non valida
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid response. Please enter valid numbers from the list of constraints, separated by commas.")


        # Condizione per gestire la risposta alla durata delle notifiche
        elif user_states[user_id] == 'awaiting_duration_response':
            # Verifico se l'utente ha inserito un numero 
            if user_message.isdigit():
                duration_minutes = int(user_message)    

                sub_period = duration_minutes

                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Great! You will receive notifications for the subscribed event for {duration_minutes} minutes.")
                
                #  E chiedo all'utente di inserire un intervallo di tempo in secondi per l'aggiornamento delle notifiche
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Please enter an interval of time in seconds for the notification updates.")

                # Aggiorno lo stato dell'utente per gestire la risposta all'intervallo di tempo
                user_states[user_id] = 'awaiting_interval_response'

                context.user_data['sub_period'] = sub_period
                
            else:
                # L'utente ha inserito una risposta non valida
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid response. Please enter a valid number for the duration in minutes.")

        # Condizione per gestire la risposta all'intervallo di tempo
        elif user_states[user_id] == 'awaiting_interval_response':
            # Verifico se l'utente ha inserito un numero
            if user_message.isdigit():
                interval_seconds = int(user_message)

                notify_freq = interval_seconds
                
                user_name=context.user_data.get('user_name', 'Unknown User'),
                user_city=context.user_data.get('user_city', 'Unknown City'),
                chat_id=update.effective_chat.id,
                tmp=context.user_data.get('tmp_constraint', False),
                feel_tmp=context.user_data.get('feel_tmp_constraint', False),
                hum=context.user_data.get('hum_constraint', False),
                weather=context.user_data.get('weather_constraint', False),
                wind=context.user_data.get('wind_constraint', False),
                sub_period=context.user_data.get('sub_period', 0),
                notify_freq=notify_freq
                
                # Pubblico i dati della sottoscrizione sul topic
                publish_on_topic(user_name, user_city, chat_id,tmp, feel_tmp, hum, weather, wind, sub_period, notify_freq)
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Great! Notifications will be updated every {interval_seconds} seconds.")
                print(f"Type: {type(sub_period)}")
                time.sleep(((sub_period[0]*60)) + 5)
                # Chiedo all'utente di inserire "stop" dopo la ricezione delle notifiche
                await context.bot.send_message(chat_id=update.effective_chat.id, text="To stop receiving notifications, type 'stop'. Otherwise, continue with your preferences.")

                # Aggiorno lo stato dell'utente per gestire la risposta alla richiesta di interrompere
                user_states[user_id] = 'awaiting_stop_response'
            else:
                # L'utente ha inserito una risposta non valida
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid response. Please enter a valid number for the interval in seconds.")

        # Condizione per gestire la risposta alla richiesta di interrompere
        elif user_states[user_id] == 'awaiting_stop_response':
            if user_message.lower() == 'stop':
             
                await context.bot.send_message(chat_id=update.effective_chat.id, text="You have successfully unsubscribed. Type /start to begin a new subscription.")
                
                # Rimuovo lo stato dell'utente
                del user_states[user_id]
            else:
                # L'utente ha inserito una risposta diversa da "stop"
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid response. Please type 'stop' to stop receiving notifications.")

        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Please use the /start command to begin.")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)

    application.add_handler(start_handler)
    application.add_handler(message_handler)

    application.run_polling()




