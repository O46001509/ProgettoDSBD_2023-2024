from flask import Flask, jsonify, request, Response
import time, logging
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import generate_latest
from create_table_functions import *
from subsriptions_funcions import *
from users_functions import *
from sla_metric_functions import *
from sla_violations_functions import *
from timelocallogging_wrapper import LocalTimeFormatter
from configuration_DB import connect_to_database


# --------------------------------------------------
formatter = LocalTimeFormatter(
    fmt='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)
# --------------------------------------------------

# Delay inserito per attendere l'avvio del servizio postgres.
time.sleep(3)

app = Flask(__name__)
metrics = PrometheusMetrics(app)

# Endpoint /metrics per esporre le metriche a Prometheus
@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')

@app.route('/crea_tabella_utenti', methods=['POST'])
def create_users():
    return create_users_table(conn, cur)

@app.route('/crea_tabella_sottoscrizioni', methods=['POST'])
def create_subscriptions():
    return create_subscriptions_table(conn, cur)
    
@app.route('/crea_tabella_sla_definitions', methods=['POST'])
def create_sla_definitions():
    return create_sla_definitions_table(conn, cur)

@app.route('/crea_tabella_sla_violations', methods=['POST'])
def create_sla_violations():
    return create_sla_violations_table(conn, cur)


# ------------------ Gestione SOTTOSCRIZIONI DB ------------------------------------

@app.route('/sottoscrizioni', methods=['GET','POST','PUT'])
def manage_subscriptions():
    if request.method == 'GET':
        return request_get_sottoscrizioni(cur)
    elif request.method == 'POST':
        return request_post_sottoscrizioni(conn, cur)
    elif request.method == 'PUT':
        return request_put_sottoscrizioni(conn, cur)

# Endpoint per verificare l'esistenza di una sottoscrizione
@app.route('/verifica_sottoscrizione', methods=['POST'])
def verify_subscription():
    return verifica_sottoscrizione(cur)

# Endpoint per cancellare una sottoscrizione
@app.route('/cancella_sottoscrizione', methods=['POST'])
def delete_subscription():
    return cancella_sottoscrizione(conn, cur)

@app.route('/notifiche', methods=['POST'])
def receive_notification():
    data = request.get_json()
    user_name = data.get('user_name')
    message = data.get('message')

    cur.execute("SELECT * FROM subscriptions WHERE user_name = %s", (user_name,))
    subscription = cur.fetchone()
    if subscription:
        print(subscription)

    return jsonify({'message': 'Notifica inviata con successo!'}), 200


# ------------------------- Gestione UTENTI DB -------------------------------------------------

@app.route('/aggiungi_utente', methods=['POST'])
def add_user():
    return aggiungi_utente(conn, cur)

@app.route('/recupera_utente', methods=['GET'])
def get_user():
    return recupera_utente(cur)
    
@app.route('/recupera_intervallo', methods=['GET'])
def get_interval():
    return recupero_intervallo(cur)

@app.route('/verifica_utente', methods=['GET'])
def verifica_utente():
    return verifica_utente_(cur)

@app.route('/aggiorna_utente', methods=['PUT'])
def update_user():
    return aggiorna_utente(conn, cur)
    
@app.route('/aggiorna_intervallo', methods=['PUT'])
def update_user_interval():
    return aggiorna_intervallo(conn, cur)

@app.route('/aggiorna_intervallo_tutti', methods=['PUT'])
def aggiorna_intervallo_tutti_endpoint():
    return aggiorna_intervallo_tutti(conn, cur)

@app.route('/recupera_intervallo_primo_utente', methods=['GET'])
def recupera_intervallo_primo_utente_endpoint():
    intervallo = recupera_intervallo_primo_utente(cur)
    if intervallo is not None:
        return jsonify({'intervallo': intervallo}), 200
    else:
        return jsonify({'error': 'Impossibile recuperare l\'intervallo del primo utente'}), 500

    
@app.route('/utenti_user_name', methods=['GET'])
def get_all_user_names():
    return get_user_names(cur)
    
@app.route('/utenti', methods=['GET'])
def get_subscriptions_by_user_name():
    try:
        user_name = request.args.get('user_name')

        if not user_name:
            return jsonify({'error': 'Specificare user_name come parametro nella richiesta'}), 400

        cur.execute("SELECT * FROM subscription WHERE user_name = %s", (user_name,))
        subscriptions = cur.fetchall()
        subscriptions_list = []

        for subscription in subscriptions:
            subscriptions_list.append({
                'subscription_id': subscription[0],
                'chat_id': subscription[1],
                'user_name': subscription[2],
            })

        return jsonify(subscriptions_list), 200
    except Exception as e:
        return jsonify({'error': f"Errore durante la richiesta delle sottoscrizioni: {e}"}), 500
    
@app.route('/chat_id', methods=['GET'])
def get_chat_id_by_user_name():
    return get_chat_id(cur)

@app.route('/recupera_primo_user_name', methods=['GET'])
def recupera_primo_user_name():
    try:
        # Seleziona l'user_name dall'utente con l'ID più basso (o un altro criterio)
        cur.execute("SELECT user_name FROM users ORDER BY id ASC LIMIT 1")
        result = cur.fetchone()
        if result:
            user_name = result[0]
            logger.info(f"User_name recuperato per il primo utente: {user_name}")
            return jsonify({'user_name': user_name}), 200
        else:
            logger.error("Nessun utente trovato nel database.")
            return jsonify({'error': "Nessun utente trovato nel database."}), 404
    except Exception as e:
        logger.error(f"Errore durante il recupero del primo user_name: {e}")
        return jsonify({'error': f"Errore durante il recupero del primo user_name: {e}"}), 500

# ----------------------- Gestione SLA-METRICS & VIOLATIONS DB ---------------------------------------

@app.route('/get_sla_metrics', methods=['GET'])
def get_sla_metrics():
    return request_get_sla_metrics(cur)

@app.route('/add_sla_metric', methods=['POST'])
def add_sla_metric():
    return aggiunta_metrica(conn, cur)

@app.route('/update_sla_metric', methods=['PUT'])
def update_sla_metric():
    return aggiorna_metrica(conn, cur)

@app.route('/delete_sla_metric', methods=['DELETE'])
def delete_sla_metric():
    return cancella_metrica(conn, cur)

@app.route('/record_sla_violation', methods=['POST'])
def record_sla_violation():
    return aggiunta_violazione(conn, cur)

@app.route('/get_sla_violations', methods=['GET'])
def get_sla_violations():
    cur.execute("SELECT * FROM sla_violations")
    sla_violations = cur.fetchall()
    return jsonify(sla_violations), 200

@app.route('/count_sla_violations', methods=['GET'])
def count_sla_violations():
    return conta_violazioni(cur)


if __name__ == '__main__':
    conn, cur = connect_to_database()
    if conn is not None:
        app.run(debug=True, host='0.0.0.0', port=5004)
        cur.close()
        conn.close()



