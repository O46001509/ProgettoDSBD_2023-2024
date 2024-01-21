from flask import Flask, request, jsonify
import psycopg2, os, time
import json
import requests


time.sleep(4)

host = os.environ.get('POSTGRES_HOST','NO VARIABLE POSTGRES_HOST'),
user = os.environ.get('POSTGRES_USER','NO VARIABLE POSTGRES_USER'),
password = os.environ.get('POSTGRES_PASSWORD','NO VARIABLE POSTGRES_PASSWORD'),
database = os.environ.get('POSTGRES_DATABASE','NO VARIABLE POSTGRES_DATABASE')

app = Flask(__name__)
DATABASE_SERVICE_URL = "http://database-service:5004"

conn = psycopg2.connect(    
        host = host[0],
        port = 5432,
        user = user[0],
        password = password[0],
        database = database)
cur = conn.cursor()

try:
    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions(
            id SERIAL PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            citta VARCHAR(50) NOT NULL,
            condizioni JSON NOT NULL
        );
    """)
    conn.commit()
except Exception as e:
    print(f"Errore durante la creazione della tabella: {e}")


subscriptions = {}

@app.route('/sottoscrizioni', methods=['GET', 'POST'])
def manage_subscriptions():
    if request.method == 'GET':
        # Restituisci l'elenco delle sottoscrizioni attuali
        return jsonify(subscriptions), 200

    elif request.method == 'POST':
        # Creazione di una nuova sottoscrizione
        
        data = request.get_json()
        response = requests.post(f"{DATABASE_SERVICE_URL}/sottoscrizioni", json=data)
        print(f"{response}")
        user_id = data.get('user_id')
        citta = data.get('citta')
        condizioni = data.get('condizioni')

        subscriptions[user_id] = {
            'citta': citta,
            'condizioni': condizioni
        }


        condizioni_json = json.dumps(condizioni)
        cur.execute("INSERT INTO subscriptions (user_id, citta, condizioni) VALUES (%s, %s, %s)",
                        (user_id, citta, condizioni_json))
        conn.commit()

        return jsonify({'message': 'Sottoscrizione creata con successo!'}), 201

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)





