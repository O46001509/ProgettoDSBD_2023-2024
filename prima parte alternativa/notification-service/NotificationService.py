from flask import Flask, request, jsonify
from telegram import Bot
from telegram.constants import ParseMode
import asyncio, os, psycopg2


app = Flask(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN_FILE", "NO_VARIABLE_FOUND")

async def send_telegram_notification(chat_id, message):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.MARKDOWN)

@app.route('/notifiche', methods=['POST'])
def receive_notification():
    data = request.get_json()
    user_id = data.get('user_id')  # Qui si ottiene il chat_id dall'utente - recupero del chat_id ancora da gestire
    message = data.get('message')
    print(f"Richiesta ricevuta - User ID: {user_id}, Messaggio: {message}")
    
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)
    # loop.run_until_complete(send_telegram_notification(chat_id=user_id, message=message))
    asyncio.run(send_telegram_notification(user_id, message))
    return jsonify({'message': 'Notifica inviata con successo!'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)




