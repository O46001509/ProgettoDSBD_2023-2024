import requests, logging, os

DATABASE_SERVICE_URL = os.environ.get('DATABASE_SERVICE_URL', 'http://database-service:5004')

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

# Aggiunta di una definizione di SLA di esempio all'avvio, per il numero di sottoscrizioni effettuate
# def add_example_sla_definition():
#     example_sla_metric = {
#         'metric_name': 'fetch_weather_requests_total',  # Nome della metrica
#         'threshold': 3,  # 
#         'description': 'Numero massimo di richieste di dati meteorologici ammesse per evitare il sovraccarico del servizio'
#     }
#     try:
#         response = requests.post(f"{DATABASE_SERVICE_URL}/add_sla_metric", json=example_sla_metric)
#         response.raise_for_status()
#         logging.info("Definizione di SLA di esempio aggiunta con successo")
#     except requests.exceptions.RequestException as e:
#         logging.error(f"Errore durante l'aggiunta della definizione di SLA di esempio: {e}")

# Aggiunta di una definizione di SLA di esempio all'avvio, per il valore dell'intervallo di notifiche     
# def add_notification_interval_sla_definition():
#     notification_interval_sla = {
#         'metric_name': 'notification_interval_seconds',  # Nome della metrica che hai definito nel weather-data-fetcher
#         'threshold': 10,  # Soglia percentuale oltre la quale si considera una violazione
#         'description': "La differenza tra l\'intervallo effettivo delle notifiche e l\'intervallo previsto non deve superare il 10%"
#     }
#     try:
#         response = requests.post(f"{DATABASE_SERVICE_URL}/add_sla_metric", json=notification_interval_sla)
#         response.raise_for_status()
#         logging.info("Definizione di SLA per l'intervallo delle notifiche aggiunta con successo")
#     except requests.exceptions.RequestException as e:
#         logging.error(f"Errore durante l'aggiunta della definizione di SLA per l'intervallo delle notifiche: {e}")