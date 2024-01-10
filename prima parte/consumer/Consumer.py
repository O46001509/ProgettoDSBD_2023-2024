import psycopg2
from kafka import KafkaConsumer
from db_operations import *

try:
    # Connessione iniziale al database
    conn, cur = initialize_database_connection()

    # Crea la tabella degli utenti se non esiste già
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            user_name VARCHAR(255) UNIQUE
        );
    """)

    # Crea la tabella delle città se non esiste già
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cities (
            id SERIAL PRIMARY KEY,
            city_name VARCHAR(255) UNIQUE
        );
    """)

    # Crea la terza tabella se non esiste già
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_city_relations (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            city_id INTEGER REFERENCES cities(id),
            CONSTRAINT unique_user_city_relation UNIQUE (user_id, city_id)
        );
    """)


    # Committa le modifiche al database
    conn.commit()

    # Chiudi la connessione iniziale al database
    close_database_connection(conn, cur)

    # Configurazione Kafka
    bootstrap_servers = 'kafka:9092'
    topic_name = 'example-topic'

    # Connessione al consumer Kafka
    consumer = KafkaConsumer(topic_name, 
                             bootstrap_servers=bootstrap_servers)

    # Connessione al database PostgreSQL
    conn, cur = initialize_database_connection()

    try:
        for message in consumer:
            user_name, city = message.value.decode('utf-8').split(',')

            try:
                user_id = insert_user(user_name)
                city_id = insert_city(city)

                if user_id and city_id:
                    insert_user_city_relation(user_id, city_id)

                    # Committa le modifiche al database
                    conn.commit()

                    # Conferma la transazione in Kafka
                    consumer.commit()

                # Esegui altre azioni se necessario...

            except Exception as e:
                # Rollback in caso di errore
                conn.rollback()
                print(f"Errore durante l'inserimento nel database: {e}")

    finally:
        # Chiudi la connessione al database e il consumer alla fine dello script
        close_database_connection(conn, cur)
        consumer.close()

except Exception as e:
    print(f"Errore generale: {e}")


