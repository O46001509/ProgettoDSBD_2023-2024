import os, time
from kafka import KafkaConsumer
from db_scripts.db_operations import *

host = os.environ.get('POSTGRES_HOST','NO VARIABLE POSTGRES_HOST'),
user = os.environ.get('POSTGRES_USER','NO VARIABLE POSTGRES_USER'),
password = os.environ.get('POSTGRES_PASSWORD','NO VARIABLE POSTGRES_PASSWORD'),
database = os.environ.get('POSTGRES_DATABASE','NO VARIABLE POSTGRES_DATABASE')

# Delay inserito per evitare che Consumer interagisca con datebase prima che servizio postgres è in esecuzione
time.sleep(10)

try:
    
    conn, cur = initialize_database_connection(host[0], user[0], password[0], database)

    create_users(cur)
    create_cities(cur)
    create_user_city_relations(cur)
    
    # Committo le modifiche al database
    conn.commit()

    close_database_connection(conn, cur)
    
    bootstrap_servers = 'kafka:9092'
    topic_name = 'example-topic'

    consumer = KafkaConsumer(topic_name, 
                             bootstrap_servers=bootstrap_servers)
   
    conn, cur = initialize_database_connection(host[0], user[0], password[0], database)
    try:
        for message in consumer:
            print(f"messaggio: {message.value.decode('utf-8')}")
            # Leggo i valori pubblicati nel topic
            user_name, city, chat_id, tmp, feel_tmp, hum, weather, wind, sub_period, notify_freq = message.value.decode('utf-8').split(",")  # Aggiunta dei campi interi
           
            try:
                user_id = insert_user(user_name, chat_id, cur)
                city_id = insert_city(city, cur, tmp, feel_tmp, hum, weather, wind)
                
                if user_id and city_id:
                    insert_user_city_relation(user_id, city_id, sub_period, notify_freq, cur) 
                    
                    conn.commit()

                    # Confermo la transazione in Kafka
                    consumer.commit()

            except Exception as e:
                # Rollback in caso di errore
                conn.rollback()
                print(f"Errore durante l'inserimento nel database: {e}")

    finally:
        # Chiudo la connessione al database e il consumer alla fine dello script
        close_database_connection(conn, cur)
        consumer.close()
except Exception as e:
    print(f"Errore generale: {e}")

    

