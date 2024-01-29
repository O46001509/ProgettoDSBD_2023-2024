from flask import Flask, request, jsonify, Response
import requests
import os, time
import logging
from datetime import datetime
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import generate_latest, Counter
from apscheduler.schedulers.background import BackgroundScheduler

logging.basicConfig(level=logging.INFO)

time.sleep(4)

app = Flask(__name__)

# Configura le metriche Prometheus
metrics = PrometheusMetrics(app)

# Configurazione microservizio database e Prometheus
DATABASE_SERVICE_URL = os.environ.get('DATABASE_SERVICE_URL', 'http://database-service:5004')
PROMETHEUS_URL = os.environ.get('PROMETHEUS_URL', 'http://prometheus:9090')

SLA_CPU_USAGE_THRESHOLD = 0.7  # 70% di utilizzo della CPU

# Inizializzazione del Scheduler per attività pianificate
scheduler = BackgroundScheduler()

def create_sla_definitions_table():
    try:
        response = requests.post(f"{DATABASE_SERVICE_URL}/crea_tabella_sla_definitions")
        response.raise_for_status()
        logging.info("Tabella della sla_definitons creata con successo")
    except requests.exceptions.RequestException as e:
        logging.error(f"Errore durante la creazione della tabella sla_definitions: {e}")

def create_sla_violations_table():
    try:
        response = requests.post(f"{DATABASE_SERVICE_URL}/crea_tabella_sla_violations")
        response.raise_for_status()
        logging.info("Tabella dell sla_violations creata con successo")
    except requests.exceptions.RequestException as e:
        logging.error(f"Errore durante la creazione della tabella sla_violations: {e}")

create_sla_definitions_table()
create_sla_violations_table()




# Endpoint /metrics per esporre le metriche a Prometheus
@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')

 #Aggiunta di una definizione di SLA di esempio all'avvio
def add_example_sla_definition():
    example_sla_metric = {
        'metric_name': 'fetch_weather_requests_total',  # Nome della metrica
        'threshold': 3,  # 
        'description': 'Numero massimo di richieste di dati meteorologici ammesse per evitare il sovraccarico del servizio'
    }
    try:
        response = requests.post(f"{DATABASE_SERVICE_URL}/add_sla_metric", json=example_sla_metric)
        response.raise_for_status()
        logging.info("Definizione di SLA di esempio aggiunta con successo")
    except requests.exceptions.RequestException as e:
        logging.error(f"Errore durante l'aggiunta della definizione di SLA di esempio: {e}")

# Endpoint per la gestione degli SLA
@app.route('/sla', methods=['POST', 'GET', 'PUT', 'DELETE'])
def manage_sla():
    if request.method == 'POST':
        # Aggiungo una nuova definizione di SLA
        data = request.get_json()
        response = requests.post(f"{DATABASE_SERVICE_URL}/add_sla_metric", json=data)
        return jsonify(response.json()), response.status_code
    
    elif request.method == 'GET':
        # Recupero le definizioni di SLA
        response = requests.get(f"{DATABASE_SERVICE_URL}/get_sla_metrics")
        return jsonify(response.json()), response.status_code
    
    elif request.method == 'PUT':
        # Aggiorno una definizione di SLA esistente
        data = request.get_json()
        response = requests.put(f"{DATABASE_SERVICE_URL}/update_sla_metric", json=data)
        return jsonify(response.json()), response.status_code
    
    elif request.method == 'DELETE':
        # Rimuovo una definizione di SLA
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

    # non siamo arrivati a implementare questa parte
    print(metric_name)

def add_notification_interval_sla_definition():
    notification_interval_sla = {
        'metric_name': 'notification_interval_seconds',  # Nome della metrica che hai definito nel weather-data-fetcher
        'threshold': 10,  # Soglia percentuale oltre la quale si considera una violazione
        'description': "La differenza tra l\'intervallo effettivo delle notifiche e l\'intervallo previsto non deve superare il 10%"
    }
    try:
        response = requests.post(f"{DATABASE_SERVICE_URL}/add_sla_metric", json=notification_interval_sla)
        response.raise_for_status()
        logging.info("Definizione di SLA per l'intervallo delle notifiche aggiunta con successo")
    except requests.exceptions.RequestException as e:
        logging.error(f"Errore durante l'aggiunta della definizione di SLA per l'intervallo delle notifiche: {e}")

add_notification_interval_sla_definition()

def fetch_metric_value(metric_name):
    try:
        prometheus_query_url = f"{PROMETHEUS_URL}/api/v1/query"
        query = {'query': metric_name}
        response = requests.get(prometheus_query_url, params=query)
        response.raise_for_status()
        data = response.json()['data']['result']
        if data:
            return data[0]['value'][1]  # Valore attuale della metrica
    except requests.exceptions.RequestException as e:
        logging.error(f"Errore durante il recupero del valore della metrica {metric_name}: {e}")
    return None

def fetch_prometheus_query(query):
    try:
        response = requests.get(f'{PROMETHEUS_URL}/api/v1/query', params={'query': query})
        response.raise_for_status()
        results = response.json()['data']['result']
        return results
    except requests.exceptions.RequestException as e:
        logging.error(f"Errore durante l'esecuzione della query Prometheus {query}: {e}")
        return []

def check_cpu_usage():
    try:
        query = 'job:cpu_usage:avg_over_time_5m'
        results = fetch_prometheus_query(query)
        for result in results:
            cpu_usage = 1 - float(result['value'][1])  # Considerando l'utilizzo come 1 - idle
            if cpu_usage > SLA_CPU_USAGE_THRESHOLD:
                logging.warning(f'Alert: High CPU usage detected: {cpu_usage * 100:.2f}%')
                # Qui dovrebbero essere implementate azioni correttive o inviare notifiche, 
                # ma non l'abbiamo fatto.
    except Exception as e:
        logging.error(f"Errore durante il controllo dell'utilizzo della CPU: {e}")

sla_violations_counter = Counter('sla_violations', 'Number of SLA violations')

def evaluate_sla():
    try:
        sla_metrics = requests.get(f"{DATABASE_SERVICE_URL}/get_sla_metrics").json()
        for metric in sla_metrics:
            metric_name = metric['metric_name']
            actual_value = fetch_metric_value(metric_name)
            threshold_percentage = metric.get('threshold', 0)  # Ottieni la soglia percentuale se definita
            
            # Controllo aggiuntivo per la metrica dell'intervallo delle notifiche
            if metric_name == 'notification_interval_seconds' and actual_value is not None:
                # Calcola l'intervallo previsto dal file
                with open('intervallo.txt', 'r') as file:
                    intervallo_previsto = int(file.read())
                intervallo_effettivo = float(actual_value)
                logging.info(f"Intervallo effettivo -->{intervallo_effettivo}")
                # Calcola la soglia assoluta (10% dell'intervallo previsto)
                threshold = intervallo_previsto * (1 + float(threshold_percentage) / 100.0)
                logging.info(f"teshold: {threshold}")
                # Controlla se l'intervallo effettivo supera la soglia
                if intervallo_effettivo > float(threshold):
                    logging.info("Violazione verificata")
                    # Incrementa il contatore di violazioni SLA
                    sla_violations_counter.inc()
                    # Resto del codice per gestire la violazione...


                    # Registra la violazione
                    violation_data = {
                        'sla_id': metric['sla_id'],
                        'violation_time': datetime.utcnow().isoformat(),  # Converto datetime in una stringa ISO
                        'actual_value': actual_value
                    }
                    requests.post(f"{DATABASE_SERVICE_URL}/record_sla_violation", json=violation_data)
                    logging.info(f"Violazione SLA: l'intervallo effettivo delle notifiche supera del {threshold_percentage}% l'intervallo previsto.")
    except Exception as e:
        logging.error(f"Errore durante la valutazione delle SLA: {e}")


# Schedulazione della valutazione SLA ad intervalli regolari
def schedule_sla_evaluation():
    with open('intervallo.txt', 'r') as file:
        intervallo_previsto = int(file.read())
    scheduler.add_job(evaluate_sla, 'interval', seconds=30)  # Esegue ogni minuto
    scheduler.add_job(check_cpu_usage, 'interval', minutes=1)  # Esegue ogni minuto
    scheduler.start()

@app.route('/sla/status', methods=['GET'])
def get_sla_status():
    try:
        sla_metrics = requests.get(f"{DATABASE_SERVICE_URL}/get_sla_metrics").json()
        sla_status = []
        for metric in sla_metrics:
            actual_value = fetch_metric_value(metric['metric_name'])
            is_violated = float(actual_value) > float(metric['threshold']) if actual_value is not None else None
            sla_status.append({
                'metric_name': metric['metric_name'],
                'actual_value': actual_value,
                'threshold': metric['threshold'],
                'is_violated': is_violated
            })
        return jsonify(sla_status), 200
    except Exception as e:
        return jsonify({'error': f"Errore durante la richiesta dello stato SLA: {e}"}), 500




@app.route('/sla/violations/count', methods=['GET'])
def get_violations_count():
    time_frame = request.args.get('time_frame', default='1h')  # Può essere '1h', '3h', '6h'
    try:
        # Chiamata all'endpoint del database_service per ottenere il conteggio delle violazioni
        response = requests.get(f"{DATABASE_SERVICE_URL}/count_sla_violations", params={'time_frame': time_frame})
        response.raise_for_status()
        violations_count = response.json()['count']  # Assumendo che la risposta includa un campo 'count'
        
        # Aggiornare il contatore Prometheus
        #sla_violations_counter.inc(violations_count)
        
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f"Errore durante la richiesta del conteggio delle violazioni SLA: {e}"}), 500



@app.route('/sla/violation_probability', methods=['GET'])
def get_violation_probability():
    metric_name = request.args.get('metric_name')
    time_frame = request.args.get('time_frame', default='30m')  # Può essere '30m', '60m', ecc.

    # Implementazione della logica per calcolare la probabilità di violazione non svolta...
    
    probability = calculate_probability_of_violation(metric_name, time_frame)
    return jsonify({'metric_name': metric_name, 'time_frame': time_frame, 'probability': probability}), 200

def calculate_probability_of_violation(metric_name, time_frame):
    # Pseudocodice per calcolare la probabilità di violazione
    probability = 0.0 
    return probability


if __name__ == '__main__':
    schedule_sla_evaluation()
    app.run(host='0.0.0.0', port=5005)