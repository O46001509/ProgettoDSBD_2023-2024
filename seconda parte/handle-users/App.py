from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import time, os
import requests
import logging

# Inizializzazione del logging
logging.basicConfig(level=logging.INFO)  # Imposta il livello di logging a INFO

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
            # Controlla se esiste già un utente con questo user_name nel database
            check_user_response = requests.get(f"{DATABASE_SERVICE_URL}/verifica_utente", params={'user_name': user_message})

            if check_user_response.status_code == 200:
                # Se l'utente esiste nel database con lo stesso user_name
                await context.bot.send_message(chat_id=update.effective_chat.id, text="This user_name already exists. Enter a new user_name.")
                return  # Interrompe ulteriori azioni
            elif check_user_response.status_code == 404:
                
                # Recupera l'utente dal database usando il chat_id
                response = requests.get(f"{DATABASE_SERVICE_URL}/recupera_utente", params={'user_name': user_message, 'chat_id': user_id})

                if response.status_code == 200:
                    user_data = response.json()
                    logging.info(f"Risposta recupero utente: {user_data.get('message', 'Messaggio non presente nel dizionario')}")
                    # Se l'utente è già presente nel database con lo stesso chat_id
                    existing_user_name = user_data.get('user_name')
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"You have already registered with the user_name: {existing_user_name}. You can continue to subscribe to new weather events.")
                    del user_states[user_id]
                elif response.status_code == 201:
                    user_data = response.json()
                    logging.info(f"Risposta recupero utente: {user_data.get('message', 'Messaggio non presente nel dizionario')}")
                    # Se l'utente è già presente nel database con lo stesso chat_id
                    existing_user_name = user_data.get('user_name')
                    # Salva il nome nell'oggetto context.user_data
                    context.user_data['user_name'] = user_message
                    user_states[user_id] = 'awaiting_response_if_update_username'
                    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"You have already registered with the user_name: {existing_user_name}. Do you want to update your user_name or keep the existing one?")
                else:
                    logging.error(f"Errore nella richiesta /recupera_utente. Codice di stato: {response.status_code}, Contenuto: {response.text}")
                    # Salva il nome nell'oggetto context.user_data
                    context.user_data['user_name'] = user_message

                    # Salva l'utente nel database
                    data = {'user_name': user_message, 'chat_id': user_id}
                    response = requests.post(f"{DATABASE_SERVICE_URL}/aggiungi_utente", json=data)
                    response.raise_for_status()

                    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Now you have registered and you can continue to subscribe to new weather events!")

                    del user_states[user_id]

            else:
                logging.error(f"Errore nella richiesta /verifica_utente. Codice di stato: {check_user_response.status_code}, Contenuto: {check_user_response.text}")
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Si è verificato un errore nel controllo del user_name. Riprova.")
                del user_states[user_id]
                return


            
        elif user_states[user_id] == 'awaiting_response_if_update_username':
            if user_message.upper() == 'YES':
                logging.error(f"risposta yes dell'utente {context.user_data.get('user_name')}")
                # Aggiorna il nome utente nel database
                update_data = {'chat_id': user_id, 'new_user_name': context.user_data.get('user_name')}
                response = requests.put(f"{DATABASE_SERVICE_URL}/aggiorna_utente", json=update_data)
                response.raise_for_status()

                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Great! You have now registered with the new username {context.user_data.get('user_name')}. You can subscribe to new weather events.")
                del user_states[user_id]
                
            elif user_message.upper() == 'NO':
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Ok. You can continue to subscribe to new weather events.")
                del user_states[user_id]
            else:
                # Risposta diversa da 'YES' o 'NO'
                await context.bot.send_message(chat_id=update.effective_chat.id, text="Please respond with 'YES' or 'NO' only.")
                # Non elimina lo stato dell'utente in modo che possa rispondere di nuovo correttamente

            
        else:
            del user_states[user_id]
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Please use the /start command to begin.")


if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)

    application.add_handler(start_handler)
    application.add_handler(message_handler)

    # Esecuzione dell'app Telegram in modo separato
    application.run_polling()




