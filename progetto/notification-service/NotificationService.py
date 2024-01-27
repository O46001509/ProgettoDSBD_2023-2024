from flask import Flask, request, jsonify, Response
from telegram import Bot
from telegram.constants import ParseMode
import asyncio, os
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import generate_latest

app = Flask(__name__)

metrics = PrometheusMetrics(app)

# Endpoint /metrics per esporre le metriche a Prometheus
@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN_FILE", "NO_VARIABLE_FOUND")

async def send_telegram_notification(chat_id, message):
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=chat_id, text=message, parse_mode=ParseMode.MARKDOWN)

@app.route('/notifiche', methods=['POST'])
def receive_notification():
    data = request.get_json()
    user_id = data.get('user_id')  # Qui si ottiene il chat_id dall'utente
    message = data.get('message')
    print(f"Richiesta ricevuta - User ID: {user_id}, Messaggio: {message}")
  
    asyncio.run(send_telegram_notification(user_id, message))
    return jsonify({'message': 'Notifica inviata con successo!'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)




