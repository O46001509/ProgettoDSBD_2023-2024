import psycopg2, os

# host = os.environ.get("POSTGRES_HOST", "nome_host")
# db = os.environ.get("POSTGRES_DB", "nome_database")
# user = os.environ.get("POSTGRES_USER", "nome_utente")
# password = os.environ.get("POSTGRES_PASSWORD", "password")

def initialize_database_connection(host, user, password, database):

    conn = psycopg2.connect(
        host = host,
        user = user,
        password = password,
        database = database
        # host = os.environ.get('POSTGRES_HOST','NO VARIABLE POSTGRES_HOST'),
        # user = os.environ.get('POSTGRES_USER','NO VARIABLE POSTGRES_USER'),
        # password = os.environ.get('POSTGRES_PASSWORD','NO VARIABLE POSTGRES_PASSWORD'),
        # database = os.environ.get('POSTGRES_DATABASE','NO VARIABLE POSTGRES_DATABASE')
    )
    cur = conn.cursor()
    return conn, cur

def close_database_connection(conn, cur):
    try:
        # Chiudi il cursore
        cur.close()
    except Exception as e:
        print(f"Errore durante la chiusura del cursore: {e}")

    try:
        # Chiudi la connessione
        conn.close()
    except Exception as e:
        print(f"Errore durante la chiusura della connessione al database: {e}")

def insert_user(user_name, conn, cur):
    #conn, cur = initialize_database_connection()

   # try:
    cur.execute("SELECT id FROM users WHERE user_name = %s;", (user_name,))
    user_id = cur.fetchone()

    if not user_id:
        cur.execute("INSERT INTO users (user_name) VALUES (%s) RETURNING id;", (user_name,))
        user_id = cur.fetchone()

    return user_id[0] if user_id else None

    # finally:
    #     close_database_connection(conn, cur)

def insert_city(city_name, conn, cur):
    #conn, cur = initialize_database_connection()

    #try:
    cur.execute("SELECT id FROM cities WHERE city_name = %s;", (city_name,))
    city_id = cur.fetchone()

    if not city_id:
        cur.execute("INSERT INTO cities (city_name) VALUES (%s) RETURNING id;", (city_name,))
        city_id = cur.fetchone()

    return city_id[0] if city_id else None

    # finally:
    #     close_database_connection(conn, cur)

def insert_user_city_relation(user_id, city_id, conn, cur):
    #conn, cur = initialize_database_connection()

   # try:
    cur.execute("INSERT INTO user_city_relations (user_id, city_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;", (user_id, city_id))

    # finally:
    #     close_database_connection(conn, cur)
