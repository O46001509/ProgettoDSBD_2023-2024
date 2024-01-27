from flask import request, jsonify
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def aggiunta_violazione(conn, cur):
    data = request.get_json()
    sla_id = data['sla_id']
    violation_time = data['violation_time']
    actual_value = data['actual_value']
    logging.info(f"Record: {actual_value}, {violation_time} ")
    
    cur.execute("INSERT INTO sla_violations (sla_id, violation_time, actual_value) VALUES (%s, %s, %s)",
                (sla_id, violation_time, actual_value))
    conn.commit()
    
    return jsonify({'message': 'SLA violation recorded successfully'}), 201

def conta_violazioni(cur):
    time_frame = request.args.get('time_frame', default='1h')  # Può essere '1h', '3h', '6h'
    try:
        query = f"""
            SELECT COUNT(*) FROM sla_violations 
            WHERE violation_time >= NOW() - INTERVAL '{time_frame}'
        """
        cur.execute(query)
        count = cur.fetchone()[0]
        return jsonify({'time_frame': time_frame, 'violations_count': count}), 200
    except Exception as e:
        return jsonify({'error': f"Errore durante la richiesta del conteggio delle violazioni SLA: {e}"}), 500