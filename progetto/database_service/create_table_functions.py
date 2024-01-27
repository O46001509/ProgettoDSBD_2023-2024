from flask import jsonify

def create_users_table(conn, cur):
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                user_name VARCHAR(255),
                chat_id INTEGER,
                interval INTEGER
            );
        """)
        conn.commit()
        return jsonify({'message': 'Tabella degli utenti creata con successo!'}), 201
    except Exception as e:
        return jsonify({'error': f"Errore durante la creazione della tabella users: {e}"}), 500
    
def create_subscriptions_table(conn, cur):
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions(
                id SERIAL PRIMARY KEY,
                user_name VARCHAR(50) NOT NULL,
                citta VARCHAR(50) NOT NULL,
                condizioni JSON NOT NULL
            );
        """)
        conn.commit()
        return jsonify({'message': 'Tabella delle sottoscrizioni creata con successo!'}), 201
    except Exception as e:
        return jsonify({'error': f"Errore durante la creazione della tabella subscriptions: {e}"}), 500
    
def create_sla_definitions_table(conn, cur):
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sla_definitions (
                sla_id SERIAL PRIMARY KEY,
                metric_name VARCHAR(255) NOT NULL,
                threshold DECIMAL NOT NULL,
                description TEXT
            );
        """ )
        conn.commit()
        return jsonify({'message': 'Tabella del sla_definitos creata con successo!'}), 201
    except Exception as e:
        return jsonify({'error': f"Errore durante la creazione della tabella sla_definitions: {e}" }), 500

def create_sla_violations_table(conn, cur):
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sla_violations ( 
                violation_id SERIAL PRIMARY KEY,
                sla_id INT NOT NULL,
                violation_time TIMESTAMP NOT NULL,
                actual_value DECIMAL NOT NULL,
                FOREIGN KEY (sla_id) REFERENCES sla_definitions(sla_id)
            );
        """)
        conn.commit()
        return jsonify({'message': 'Tabella sla_violations creata con successo!'}), 201
    except Exception as e:
        return jsonify({'error': f"Errore durante la creazione della tabella sla_violations: {e}"}), 500