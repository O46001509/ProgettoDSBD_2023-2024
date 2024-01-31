import os, logging
import psycopg2

host = os.environ.get('POSTGRES_HOST','NO VARIABLE POSTGRES_HOST'),
user = os.environ.get('POSTGRES_USER','NO VARIABLE POSTGRES_USER'),
password = os.environ.get('POSTGRES_PASSWORD','NO VARIABLE POSTGRES_PASSWORD'),
database = os.environ.get('POSTGRES_DATABASE','NO VARIABLE POSTGRES_DATABASE')


def connect_to_database():
    # required_params = [host[0], user[0], password[0], database]

    # if all(required_params):
    #     # Procedi con la connessione al database
    # try:
        conn = psycopg2.connect(
            host=host[0],
            port=5432,
            user=user[0],
            password=password[0],
            database=database)
        cur = conn.cursor()
        print("Connessione al database riuscita!")
        return conn, cur
    # except Exception as e:
    #     print(f"Errore durante la connessione al database: {e}")
    #     return None, None
    # else:
    #     print("Alcuni parametri di connessione al database mancano. Impossibile connettersi.")
    #     return None, None

