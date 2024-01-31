from flask import request, jsonify
import requests, logging, os

DATABASE_SERVICE_URL = os.environ.get('DATABASE_SERVICE_URL', 'http://database-service:5004')

def added_sla_to_the_db():
    try:
        # Aggiungo una nuova definizione di SLA
        data = request.get_json()
        response = requests.post(f"{DATABASE_SERVICE_URL}/add_sla_metric", json=data)
        return jsonify(response.json()), response.status_code
    except Exception as e:
            return jsonify({'error': f"Errore durante la richiesta dello di aggiunta sla: {e}"}), 500

def obtaining_sla_from_the_db():
    # Recupero le definizioni di SLA
    try:
        response = requests.get(f"{DATABASE_SERVICE_URL}/get_sla_metrics")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logging.error(f"Eccezione durante l'aggiornamento SLA: {e}")
        return jsonify({'error': f"Errore interno del server durante l'aggiornamento SLA: {e}"}), 500

def update_sla_in_the_db():
    try:
        data = request.get_json()
        logging.info(f"Invio richiesta di aggiornamento SLA al database service: {data}")
        response = requests.put(f"{DATABASE_SERVICE_URL}/update_sla_metric", json=data)
        
        # Controllo se la risposta dal database service è positiva 
        if response.status_code == 200:
            logging.info(f"Risposta positiva dal database service: {response.json()}")
            return jsonify(response.json()), 200
        else:
            # Gestisco il caso in cui il database service restituisca un errore
            logging.error(f"Errore nella risposta dal database service: {response.json()}")
            return jsonify(response.json()), response.status_code
    except Exception as e:
        logging.error(f"Eccezione durante l'aggiornamento SLA: {e}")
        return jsonify({'error': f"Errore interno del server durante l'aggiornamento SLA: {e}"}), 500


def deleting_sla_from_the_db():
    # Rimuovo una definizione di SLA
    try:
        data = request.get_json()
        response = requests.delete(f"{DATABASE_SERVICE_URL}/delete_sla_metric", json=data)
        return jsonify(response.json()), response.status_code
    except Exception as e:
        logging.error(f"Eccezione durante l'aggiornamento SLA: {e}")
        return jsonify({'error': f"Errore interno del server durante l'aggiornamento SLA: {e}"}), 500
    
def register_violation(violation_data):
    requests.post(f"{DATABASE_SERVICE_URL}/record_sla_violation", json=violation_data)
    