from flask import jsonify, request
import logging
from timelocallogging_wrapper import LocalTimeFormatter

# ---------------------------------------------------
formatter = LocalTimeFormatter(
    fmt='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(handler)
# ---------------------------------------------------

def request_get_sla_metrics(cur):
    try:
        cur.execute("SELECT * FROM sla_definitions")
        sla_metrics = cur.fetchall()
        
        # Converto i risultati in un formato più leggibile
        sla_metrics_list = []
        for metric in sla_metrics:
            sla_metrics_list.append({
                'sla_id': metric[0],
                'metric_name': metric[1],
                'threshold': metric[2],
                'description': metric[3]
            })
        
        logger.info(f"SLA_metrics: {sla_metrics_list}")
        return jsonify(sla_metrics_list), 200
    except Exception as e:
        logger.error(f"Errore durante il recupero delle metriche SLA: {e}")
        return jsonify({'error': f"Errore durante il recupero delle metriche SLA: {e}"}), 500
    
def aggiorna_metrica(conn, cur):
    data = request.get_json()
    sla_id = data['sla_id']
    metric_name = data['metric_name']
    threshold = data['threshold']
    description = data['description']
    
    cur.execute("UPDATE sla_definitions SET metric_name = %s, threshold = %s, description = %s WHERE sla_id = %s",
                (metric_name, threshold, description, sla_id))
    conn.commit()
    
    return jsonify({'message': 'SLA metric updated successfully'}), 200

def cancella_metrica(conn, cur):
    data = request.get_json()
    sla_id = data['sla_id']
    
    try:
        # Prima elimino tutte le violazioni associate alla metrica...
        cur.execute("DELETE FROM sla_violations WHERE sla_id = %s", (sla_id,))
        conn.commit()
        
        # ...poi elimino la metrica stessa, poiché le due tabelle, sla_definitions 
        # e sla_violations.
        cur.execute("DELETE FROM sla_definitions WHERE sla_id = %s", (sla_id,))
        conn.commit()
        
        return jsonify({'message': 'SLA metric and associated violations deleted successfully'}), 200
    except Exception as e:
        # Se qualcosa va storto, logga l'errore e restituisci un messaggio di errore
        logging.error(f"Errore durante l'eliminazione della metrica SLA e delle violazioni associate: {e}")
        return jsonify({'error': f"Errore durante l'eliminazione della metrica SLA e delle violazioni associate: {e}"}), 500


def aggiunta_metrica(conn, cur):
    data = request.get_json()
    metric_name = data.get('metric_name')
    threshold = data.get('threshold')
    description = data.get('description')

    if not all([metric_name, threshold, description]):
        return jsonify({'error': 'Mancano dati necessari per aggiungere una metrica SLA.'}), 400

    try:
        cur.execute("""
            INSERT INTO sla_definitions (metric_name, threshold, description)
            VALUES (%s, %s, %s)
            """, (metric_name, threshold, description))
        conn.commit()
        return jsonify({'message': 'Metrica SLA aggiunta con successo'}), 201
    except Exception as e:
        conn.rollback()  # Annullare la transazione in caso di errore
        return jsonify({'error': f"Errore durante l'aggiunta della metrica SLA: {e}"}), 500