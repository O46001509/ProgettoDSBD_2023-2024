from flask import Flask, request, jsonify, Response
import requests
import os, time, logging
from datetime import datetime

from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import generate_latest, Counter

from apscheduler.schedulers.background import BackgroundScheduler

from timelocallogging_wrapper import LocalTimeFormatter

from create_table_sla import *
from manage_sla_functions import *



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

# attesa nel caso in cui il database-service debba ancora avviarsi.
time.sleep(4)

app = Flask(__name__)

metrics = PrometheusMetrics(app)

# Configurazione microservizio database e Prometheus
DATABASE_SERVICE_URL = os.environ.get('DATABASE_SERVICE_URL', 'http://database-service:5004')
PROMETHEUS_URL = os.environ.get('PROMETHEUS_URL', 'http://prometheus:9090')

# soglia di default
SLA_MEMORY_USAGE_THRESHOLD_MB = 100

# Inizializzazione del Scheduler per le attività pianificate
# deljob evaluate_sla.
scheduler = BackgroundScheduler()

# creazione delle tabelle di metriche e vuiolazioni
create_sla_definitions_table()
create_sla_violations_table()

# Creazione metrica che può essere selezionata dall'UI di Prometheus
# come usage_memory_by_service_total,
# per visualizzare le violazioni di memoria. 
sla_violations_counters = Counter(
    'usage_memory_by_service',
    'Number of active weather subscriptions'
)
sla_violations_counter = Counter('sla_violations', 'Number of SLA violations')


@app.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype='text/plain')

# API per la creazione, l'aggiornamento, la cancellazione e la verifica di metriche SLA
@app.route('/sla', methods=['POST', 'GET', 'PUT', 'DELETE'])
def manage_sla():
    if request.method == 'POST':
        return added_sla_to_the_db()
    elif request.method == 'GET':
        return obtaining_sla_from_the_db()
    elif request.method == 'PUT':
        return update_sla_in_the_db()
    elif request.method == 'DELETE':
        return deleting_sla_from_the_db()
    else:
        return jsonify({'error': 'Metodo non supportato'}), 405


@app.route('/sla/violations', methods=['GET'])
def sla_violations():
    # Implemento la funzionalità di recupero del numero di violazioni SLA
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

# Funzione per recuperare il valore attuale da Prometheus
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
        logger.error(f"Errore durante il recupero del valore della metrica {metric_name}: {e}")
    return None

# Funzione per il recupero dell'uso della memoria
def fetch_prometheus_query(query):
    try:
        response = requests.get(f'{PROMETHEUS_URL}/api/v1/query', params={'query': query})
        response.raise_for_status()
        results = response.json()['data']['result']
        
        return results
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Errore durante l'esecuzione della query Prometheus {query}: {e}")
        return []
    
def fetch_container_memory_usage(container_name):
    try:
        query = f'container_memory_usage_bytes{{container_label_com_docker_compose_service="{container_name}"}}'
        results = fetch_prometheus_query(query)
        logger.info(f"Result{results}")
        if results:
            memory_usage_bytes = float(results[0]['value'][1])  # Valore attuale dell'utilizzo della memoria in byte
            return memory_usage_bytes
    except requests.exceptions.RequestException as e:
        logger.error(f"Errore durante il recupero dell'utilizzo della memoria del container {container_name}: {e}")
    return None



def check_memory_usage(threshold, sla_id):
    try:
        memory_usage_bytes = fetch_container_memory_usage('notification-service')
        mem_stamp = memory_usage_bytes / (1024 ** 2) # Conversione in MB
        logger.info(f"Mem -->{mem_stamp}")
        if memory_usage_bytes and (memory_usage_bytes / (1024 ** 2)) > threshold:
            logger.warning(f'Alert: High memory usage detected for container: {memory_usage_bytes / (1024 ** 2):.2f} MB')

            
            sla_violations_counters.inc()

            violation_data = {
                            'sla_id': sla_id,
                            'violation_time': datetime.utcnow().isoformat(),
                            'actual_value': memory_usage_bytes
                        }
            requests.post(f"{DATABASE_SERVICE_URL}/record_sla_violation", json=violation_data)
            logger.info(f"Violazione SLA: l'utilizzo della memoria del notification-service supera i {threshold} MB")
    except Exception as e:
        logger.error(f"Errore durante il controllo dell'utilizzo della memoria del container: {e}")

# Per ogni metrica SLA inserita, controlliamo se la soglia rispettata.
# Se non lo è, crea una violazione.  
def evaluate_sla():
    try:
        sla_metrics = requests.get(f"{DATABASE_SERVICE_URL}/get_sla_metrics").json()
        logger.info(f"Lista metriche-->{sla_metrics}")
        
        for metric in sla_metrics:
            metric_name = metric['metric_name']
            threshold = metric.get('threshold', 0)  # Ottengo la soglia se definita
          
            if metric_name == 'notification_interval_seconds':
                actual_value = fetch_metric_value(metric_name)
                
                if actual_value is not None:
                    intervallo_effettivo = float(actual_value)
                    with open('intervallo.txt', 'r') as file:
                        intervallo_previsto = int(file.read())
                    intervallo_effettivo = float(actual_value)
                    logger.info(f"Metric-->{metric}")
                    logger.info(f"Intervallo effettivo -->{intervallo_effettivo}")
                    # Calcolo la soglia assoluta (ex: 10% dell'intervallo previsto)
                    threshold = intervallo_previsto * (1 + float(threshold) / 100.0)
                    logger.info(f"teshold: {threshold}")
                    
                
                    # Controllo se l'intervallo effettivo supera la soglia
                    if intervallo_effettivo > float(threshold):
                        logger.info("Violazione verificata")
                        sla_violations_counter.inc()
                        # Registro la violazione
                        violation_data = {
                            'sla_id': metric['sla_id'],
                            'violation_time': datetime.utcnow().isoformat(),
                            'actual_value': actual_value
                        }
                        requests.post(f"{DATABASE_SERVICE_URL}/record_sla_violation", json=violation_data)
                        logger.info(f"Violazione SLA: l'intervallo effettivo delle notifiche supera del {threshold}% l'intervallo previsto.")
            
            elif metric_name == 'usage_memory_by_service':
            
                s_id = metric['sla_id']
                check_memory_usage(float(threshold),s_id)
            

    except Exception as e:
        logger.error(f"Errore durante la valutazione delle SLA: {e}")


# Schedulazione della valutazione SLA ad intervalli regolari. 
# Il job evaluate_sla elabora periodicamente se ci sono violazioni.

def schedule_sla_evaluation():
    scheduler.add_job(evaluate_sla, 'interval', seconds=30)  # Esegue ogni 30s
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


def calculate_probability_of_violation(metric_name, time_frame):
    # Pseudocodice per calcolare la probabilità di violazione
    probability = 0.0 
    return probability

@app.route('/sla/violation_probability', methods=['GET'])
def get_violation_probability():
    metric_name = request.args.get('metric_name')
    time_frame = request.args.get('time_frame', default='30m')  # Può essere '30m', '60m', ecc.

    # Implementazione della logica per calcolare la probabilità di violazione non svolta...
    
    probability = calculate_probability_of_violation(metric_name, time_frame)
    return jsonify({'metric_name': metric_name, 'time_frame': time_frame, 'probability': probability}), 200


if __name__ == '__main__':
    schedule_sla_evaluation()
    app.run(host='0.0.0.0', port=5005)