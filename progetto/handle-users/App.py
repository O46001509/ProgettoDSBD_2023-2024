from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import time, os, logging
import requests
from timelocallogging_wrapper import LocalTimeFormatter


# ----------------------------------------------------
formatter = LocalTimeFormatter(
    fmt='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)
# ----------------------------------------------------

# attesa nel caso in cui il database-service debba ancora avviarsi.
time.sleep(4)

DATABASE_SERVICE_URL = "http://database-service:5004"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN_FILE", "NO_VARIABLE_FOUND")

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
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, insert your user_name!")

# Handler per gestire i messaggi di testo
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text

    if user_id in user_states:
        if user_states[user_id] == 'awaiting_name':
            # Controllo se esiste già un utente con questo user_name nel database.
            check_user_response = requests.get(f"{DATABASE_SERVICE_URL}/verifica_utente", params={'user_name': user_message})

            if check_user_response.status_code == 200:
                # Se l'utente esiste nel database con lo stesso user_name...
                await context.bot.send_message(chat_id=update.effective_chat.id, text="This user_name already exists. Enter a new user_name if you want, else enter a new user_name and then answer NO.")
                return  # Interrompe ulteriori azioni
            elif check_user_response.status_code == 404:
                
                # ...recupero l'utente dal database usando il chat_id.
                response = requests.get(f"{DATABASE_SERVICE_URL}/recupera_utente", params={'user_name': user_message, 'chat_id': user_id})

                if response.status_code == 200:
                    user_data = response.json()
                    logger.info(f"handle-users --> Risposta recupero utente: {user_data.get('message', 'Messaggio non presente nel dizionario')}")
                    # Se l'utente è già presente nel database con lo stesso chat_id...
                    existing_user_name = user_data.get('user_name')
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"You have already registered with the user_name: {existing_user_name}. You can continue to subscribe to new weather events.")
                    del user_states[user_id]
                elif response.status_code == 201:
                    user_data = response.json()
                    logger.info(f"handle-users --> Risposta recupero utente: {user_data.get('message', 'Messaggio non presente nel dizionario')}")
                    # Se l'utente non è già presente nel database con lo stesso chat_id...
                    existing_user_name = user_data.get('user_name')
                    # ...salvo il nome utente nell'oggetto context.user_data.
                    context.user_data['user_name'] = user_message
                    user_states[user_id] = 'awaiting_response_if_update_username'
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"You have already registered with the user_name: {existing_user_name}. Do you want to update your user_name or keep the existing one?")

                else:
                    logger.error(f"handle-users --> Errore nella richiesta /recupera_utente. Codice di stato: {response.status_code}, Contenuto: {response.text}")
                    
                    context.user_data['user_name'] = user_message
                    user_states[user_id] = 'awaiting_response_interval'
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"How often do you want to recive notifications of your subscriptions? Insert it in seconds.")

            else:
                logger.error(f"handle-users --> Errore nella richiesta /verifica_utente. Codice di stato: {check_user_response.status_code}, Contenuto: {check_user_response.text}")
                await context.bot.send_message(chat_id=update.effective_chat.id, text="An error occurred in cheking the user_name. Try again with /start.")
                del user_states[user_id]
                return

        elif user_states[user_id] == 'awaiting_response_interval':
             # Verifico se l'utente ha inserito un numero 
            if user_message.isdigit():
                duration = int(user_message)    
                
                 # Salvo l'intervallo nel database
                data = {'user_name': context.user_data['user_name'], 'chat_id': user_id, 'interval': duration}
                response = requests.post(f"{DATABASE_SERVICE_URL}/aggiungi_utente", json=data)
                response.raise_for_status()

                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Great! You will receive notifications for the subscribed event for {duration} seconds.")
                context.user_data['interval'] = duration
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Now you have registered and you can continue to subscribe to new weather events!")
            
                del user_states[user_id]
            else:
                # L'utente ha inserito una risposta non valida
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid response. Please enter a valid number for the duration in seconds.")
            
        elif user_states[user_id] == 'awaiting_response_if_update_username':
            # Recupero l'intervallo dall'utente specifico dal database
            try:
                user_data_response = requests.get(f"{DATABASE_SERVICE_URL}/recupera_intervallo", params={'chat_id': user_id})
                user_data_response.raise_for_status()
                user_data = user_data_response.json()

                # Memorizzo l'intervallo in context.user_data per un accesso più rapido
                context.user_data['interval'] = user_data.get('interval', 'Not set yet')

                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Your current notification interval is {context.user_data['interval']} seconds. Do you want to update your interval or keep the existing one?")

            except requests.exceptions.RequestException as e:
                logger.error(f"handle-users --> Errore durante il recupero dell'intervallo dell'utente: {e}")
                await context.bot.send_message(chat_id=update.effective_chat.id, text="An error occurred while fetching your notification interval. Please try again later.")
                del user_states[user_id]
                return

            if user_message.upper() == 'YES':

                logger.error(f"handle-users --> risposta yes dell'utente {context.user_data.get('user_name')}")
                # Aggiorno il nome utente nel database
                update_data = {'chat_id': user_id, 'new_user_name': context.user_data.get('user_name')}
                response = requests.put(f"{DATABASE_SERVICE_URL}/aggiorna_utente", json=update_data)
                response.raise_for_status()

                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Great! You have now registered with the new username {context.user_data.get('user_name')}. You can subscribe to new weather events.")
                user_states[user_id] = 'awaiting_response_if_update_interval'
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"You have interval =  {context.user_data['interval']}.  Do you want to update your interval or keep the existing one?")

            elif user_message.upper() == 'NO':
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Ok. You can continue to subscribe to new weather events.")
                user_states[user_id] = 'awaiting_response_if_update_interval'
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"You have interval =  {context.user_data['interval']}.  Do you want to update your interval or keep the existing one?")

            else:
                # Risposta diversa da 'YES' o 'NO'
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Please respond with 'YES' or 'NO' only.")
                return
                # Non elimino lo stato dell'utente in modo che possa rispondere di nuovo correttamente
            

        
        elif user_states[user_id] == 'awaiting_response_if_update_interval':
            if user_message.upper() == 'YES':
                user_states[user_id] = 'awaiting_response_update_interval'
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"How often do you want to recive notifications of your subscriptions? Insert it in seconds.")
            elif user_message.upper() == 'NO':
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Ok. You can continue to subscribe to new weather events with your interval {context.user_data.get('interval')}.")
                del user_states[user_id]
            else:
                # Risposta diversa da 'YES' o 'NO'
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Please respond with 'YES' or 'NO' only.")
        
        elif user_states[user_id] == 'awaiting_response_update_interval':
             # Verifico se l'utente ha inserito un numero 
            if user_message.isdigit():
                duration = int(user_message)    
                
                 # Salvo l'utente nel database
                data = {'chat_id':user_id, 'user_name': context.user_data['user_name'], 'interval': duration}
                response = requests.put(f"{DATABASE_SERVICE_URL}/aggiorna_intervallo", json=data)
                response.raise_for_status()

                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Great! You will receive notifications for the subscribed event for {duration} second.")
                
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"You can continue to subscribe to new weather events!")
            
                del user_states[user_id]
            else:
                # L'utente ha inserito una risposta non valida
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Invalid response. Please enter a valid number for the duration in seconds.")

        else:
            del user_states[user_id]
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Please use the /start command to begin.")


if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)

    application.add_handler(start_handler)
    application.add_handler(message_handler)

    '''
    Il bot rimane in ascolto per i messaggi in arrivo e
    controlla costantemente se ci sono nuovi aggiornamenti 
    (messaggi, comandi, ecc.) inviati al bot da parte degli 
    utenti su Telegram. Quando un aggiornamento viene rilevato, 
    il bot lo elabora e risponde di conseguenza in base agli 
    handler, CommandHandler e MessageHandler, che abbiamo configurato 
    sopra. 
    '''
    application.run_polling()




