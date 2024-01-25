from flask import Flask, request, jsonify, abort
import requests
import os, time
import logging
from datetime import datetime, timedelta


app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
time.sleep(4)
# Configurazione microservizio database e Prometheus
DATABASE_SERVICE_URL = os.environ.get('DATABASE_SERVICE_URL', 'http://database-service:5004')
PROMETHEUS_URL = os.environ.get('PROMETHEUS_URL', 'http://prometheus:9090')


def create_sla_definitions_table():
    try:
        response = requests.post(f"{DATABASE_SERVICE_URL}/crea_tabella_sla_definitions")
        response.raise_for_status()  # Solleva un'eccezione per codici di stato HTTP diversi da 2xx
        logging.info("Tabella della sla_definitons creata con successo")
    except requests.exceptions.RequestException as e:
        logging.error(f"Errore durante la creazione della tabella sla_definitions: {e}")

def create_sla_violations_table():
    try:
        response = requests.post(f"{DATABASE_SERVICE_URL}/crea_tabella_sla_violations")
        response.raise_for_status()  # Solleva un'eccezione per codici di stato HTTP diversi da 2xx
        logging.info("Tabella dell sla_violations creata con successo")
    except requests.exceptions.RequestException as e:
        logging.error(f"Errore durante la creazione della tabella sla_violations: {e}")

create_sla_definitions_table()
create_sla_violations_table()

 #Aggiunta di una definizione di SLA di esempio all'avvio
def add_example_sla_definition():
    example_sla_metric = {
        'metric_name': 'response_time',  # Nome della metrica
        'threshold': 0.300,  # Soglia di 300ms per il tempo di risposta
        'description': 'Tempo massimo di risposta accettabile'
    }
    try:
        response = requests.post(f"{DATABASE_SERVICE_URL}/add_sla_metric", json=example_sla_metric)
        response.raise_for_status()
        logging.info("Definizione di SLA di esempio aggiunta con successo")
    except requests.exceptions.RequestException as e:
        logging.error(f"Errore durante l'aggiunta della definizione di SLA di esempio: {e}")

add_example_sla_definition()

# Endpoint per la gestione degli SLA
@app.route('/sla', methods=['POST', 'GET', 'PUT', 'DELETE'])
def manage_sla():
    if request.method == 'POST':
        # Aggiungi una nuova definizione di SLA
        data = request.get_json()
        response = requests.post(f"{DATABASE_SERVICE_URL}/add_sla_metric", json=data)
        return jsonify(response.json()), response.status_code
    
    elif request.method == 'GET':
        # Recupera le definizioni di SLA
        response = requests.get(f"{DATABASE_SERVICE_URL}/get_sla_metrics")
        return jsonify(response.json()), response.status_code
    
    elif request.method == 'PUT':
        # Aggiorna una definizione di SLA esistente
        data = request.get_json()
        response = requests.put(f"{DATABASE_SERVICE_URL}/update_sla_metric", json=data)
        return jsonify(response.json()), response.status_code
    
    elif request.method == 'DELETE':
        # Rimuovi una definizione di SLA
        data = request.get_json()
        response = requests.delete(f"{DATABASE_SERVICE_URL}/delete_sla_metric", json=data)
        return jsonify(response.json()), response.status_code

# Endpoint per la visualizzazione delle violazioni SLA
@app.route('/sla/violations', methods=['GET'])
def sla_violations():
    # Implementazione della funzionalità di recupero del numero di violazioni SLA
    response = requests.get(f"{DATABASE_SERVICE_URL}/get_sla_violations")
    return jsonify(response.json()), response.status_code

# Endpoint per la probabilità di violazione SLA
@app.route('/sla/probability', methods=['GET'])
def sla_probability():
    metric_name = request.args.get('metric_name')
    # Calcola la probabilità di violazione per la metrica specificata
    # Questo richiederà probabilmente un modello statistico o storico basato sui dati passati
    # Pseudocodice:
    # probability = calculate_probability_of_violation(metric_name)
    # return jsonify({'metric_name': metric_name, 'probability': probability})

# Funzione per recuperare il valore attuale di una metrica da Prometheus
def fetch_metric_value(metric_name):
    # Recupera il valore attuale di una metrica da Prometheus
    prometheus_query_url = f"{PROMETHEUS_URL}/api/v1/query"
    query = {'query': metric_name}
    response = requests.get(prometheus_query_url, params=query)
    if response.status_code == 200:
        data = response.json()['data']['result']
        if data:
            return data[0]['value'][1]  # Valore attuale della metrica
    return None

def evaluate_sla():
    # Valuta tutte le metriche SLA rispetto ai valori attuali
    sla_metrics = requests.get(f"{DATABASE_SERVICE_URL}/get_sla_metrics").json()
    for metric in sla_metrics:
        metric_name = metric['metric_name']
        actual_value = fetch_metric_value(metric_name)
        
        if actual_value and float(actual_value) > metric['threshold']:
            # Registra la violazione
            violation_data = {
                'sla_id': metric['sla_id'],
                'violation_time': datetime.utcnow(),
                'actual_value': actual_value
            }
            requests.post(f"{DATABASE_SERVICE_URL}/record_sla_violation", json=violation_data)
            logging.info(f"Violazione SLA registrata: {metric_name} con valore {actual_value}")

# Schedulazione della valutazione SLA ad intervalli regolari
def schedule_sla_evaluation():
    # Schedula la valutazione SLA ad intervalli regolari
    # Questo potrebbe essere implementato utilizzando APScheduler o un ciclo while con sleep
    # Pseudocodice:
    # while True:
    #     evaluate_sla()
    #     time.sleep(INTERVAL)
    pass

@app.route('/sla/status', methods=['GET'])
def get_sla_status():
    try:
        sla_metrics = requests.get(f"{DATABASE_SERVICE_URL}/get_sla_metrics").json()
        sla_status = []
        for metric in sla_metrics:
            actual_value = fetch_metric_value(metric['metric_name'])
            is_violated = float(actual_value) > metric['threshold'] if actual_value is not None else None
            sla_status.append({
                'metric_name': metric['metric_name'],
                'actual_value': actual_value,
                'threshold': metric['threshold'],
                'is_violated': is_violated
            })
        return jsonify(sla_status), 200
    except Exception as e:
        return jsonify({'error': f"Errore durante la richiesta dello stato SLA: {e}"}), 500

# In SLAManager.py

@app.route('/sla/violations/count', methods=['GET'])
def get_violations_count():
    time_frame = request.args.get('time_frame', default='1h')  # Può essere '1h', '3h', '6h'
    try:
        # Chiamata all'endpoint del database_service per ottenere il conteggio delle violazioni
        response = requests.get(f"{DATABASE_SERVICE_URL}/count_sla_violations", params={'time_frame': time_frame})
        response.raise_for_status()  # Solleva un'eccezione per codici di stato HTTP diversi da 2xx
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f"Errore durante la richiesta del conteggio delle violazioni SLA: {e}"}), 500



@app.route('/sla/violation_probability', methods=['GET'])
def get_violation_probability():
    metric_name = request.args.get('metric_name')
    time_frame = request.args.get('time_frame', default='30m')  # Può essere '30m', '60m', ecc.
    # Implementare la logica per calcolare la probabilità di violazione
    # Questo potrebbe implicare l'uso di modelli statistici o di machine learning
    probability = calculate_probability_of_violation(metric_name, time_frame)
    return jsonify({'metric_name': metric_name, 'time_frame': time_frame, 'probability': probability}), 200

def calculate_probability_of_violation(metric_name, time_frame):
    # Pseudocodice per calcolare la probabilità di violazione
    # Implementare la logica del modello qui
    probability = 0.0  # Sostituire con il calcolo effettivo
    return probability


if __name__ == '__main__':
    schedule_sla_evaluation()
    app.run(host='0.0.0.0', port=5005)