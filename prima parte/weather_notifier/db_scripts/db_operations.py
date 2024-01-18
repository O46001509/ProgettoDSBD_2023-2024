import psycopg2

def initialize_database_connection(host, user, password, database):

    conn = psycopg2.connect(
        host = host,
        user = user,
        password = password,
        database = database

    )
    cur = conn.cursor()
    return conn, cur

def close_database_connection(conn, cur):
    try:
        cur.close()
    except Exception as e:
        print(f"Errore durante la chiusura del cursore: {e}")

    try:
        conn.close()
    except Exception as e:
        print(f"Errore durante la chiusura della connessione al database: {e}")

def leggi_ricerche(cur):
    mappa_ricerche = {}

    # Query per ottenere tutte le righe dalla tabella "user_city_relations"
    query = """
        SELECT user_id, city_id, sub_period, notify_freq
        FROM user_city_relations;
    """
    cur.execute(query)

    risultati = cur.fetchall()

    # Elaborazione dei risultati
    for risultato in risultati:
        user_id, city_id, sub_period, notify_freq = risultato
        if user_id not in mappa_ricerche:
            mappa_ricerche[user_id] = []
        mappa_ricerche[user_id].append({
            'city_id': city_id,
            'sub_period': sub_period,
            'notify_freq': notify_freq
        })

    last_search = []
    if len(risultati) > 0: 
        last_search = list(risultati)[-1]
    return mappa_ricerche, last_search

def get_city_info(cur, city_id):
    cur.execute("""
        SELECT city_name, tmp, feel_tmp, hum, weather, wind
        FROM cities
        WHERE id = %s;
    """, (city_id,))
    result = cur.fetchone()
    
    if result:
        city_name, tmp, feel_tmp, hum, weather, wind = result

        city_constraints =  [tmp, feel_tmp, hum, weather, wind]
        return city_name, city_constraints
    else:
        return None, None

def get_chat_id_for_user(cur, user_id):
    cur.execute("""
        SELECT chat_id
        FROM users
        WHERE id = %s;
    """, (user_id,))
    result = cur.fetchone()
    
    if result:
        return result[0]
    else:
        return None
    
def svuota_tabelle(conn, cur):
    try:
        # Elimino tutti i dati dalla tabella "user_city_relations"
        cur.execute("DELETE FROM user_city_relations;")
        cur.execute("DELETE FROM cities;")
        cur.execute("DELETE FROM users;")

        # Resetto ID 
        cur.execute("ALTER SEQUENCE user_city_relations_id_seq RESTART WITH 1;")
        cur.execute("ALTER SEQUENCE cities_id_seq RESTART WITH 1;")
        cur.execute("ALTER SEQUENCE users_id_seq RESTART WITH 1;")

        conn.commit()

        print("Tabelle svuotate con successo.")
    except Exception as e:
        conn.rollback()
        print(f"Errore durante lo svuotamento delle tabelle: {e}")
    finally:
        close_database_connection(conn,cur)
