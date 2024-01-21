from flask import Flask, jsonify
import requests
import psycopg2, time, os

time.sleep(3)

host = os.environ.get('POSTGRES_HOST','NO VARIABLE POSTGRES_HOST'),
user = os.environ.get('POSTGRES_USER','NO VARIABLE POSTGRES_USER'),
password = os.environ.get('POSTGRES_PASSWORD','NO VARIABLE POSTGRES_PASSWORD'),
database = os.environ.get('POSTGRES_DATABASE','NO VARIABLE POSTGRES_DATABASE')

app = Flask(__name__)
conn = psycopg2.connect(    
        host = host[0],
        port = 5432,
        user = user[0],
        password = password[0],
        database = database)
cur = conn.cursor()


@app.route('/sottoscrizioni', methods=['POST'])
def create_subscription():
    data = requests.get_json()
    user_id = data.get('user_id')
    citta = data.get('citta')
    condizioni = data.get('condizioni')

    cur.execute("INSERT INTO subscriptions (user_id, citta, condizioni) VALUES (%s, %s, %s)",
                (user_id, citta, condizioni))
    conn.commit()

    return jsonify({'message': 'Sottoscrizione creata con successo!'}), 201

@app.route('/notifiche', methods=['POST'])
def receive_notification():
    data = requests.get_json()
    user_id = data.get('user_id')
    message = data.get('message')

    cur.execute("SELECT * FROM subscriptions WHERE user_id = %s", (user_id,))
    subscription = cur.fetchone()
    if subscription:
        # Invio notifica all'utente usando le informazioni della sottoscrizione
        # ... ancora da gestire e vedere se usare
        print(subscription)

    return jsonify({'message': 'Notifica inviata con successo!'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5004)






    