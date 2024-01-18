import psycopg2

# Connessione al datebase 
def initialize_database_connection(host, user, password, database):

    conn = psycopg2.connect(
        host = host,
        user = user,
        password = password,
        database = database

    )
    cur = conn.cursor()
    return conn, cur

# Chiusura della connessione
def close_database_connection(conn, cur):
    try:
        cur.close()
    except Exception as e:
        print(f"Errore durante la chiusura del cursore: {e}")

    try:
        conn.close()
    except Exception as e:
        print(f"Errore durante la chiusura della connessione al database: {e}")

def create_users(cur):
    # Creo la tabella degli utenti se non esiste già
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            user_name VARCHAR(255),
            chat_id INTEGER  
        );
    """)

def create_cities(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cities (
            id SERIAL PRIMARY KEY,
            city_name VARCHAR(255),
            tmp BOOLEAN,
            feel_tmp BOOLEAN,
            hum BOOLEAN,
            weather BOOLEAN,
            wind BOOLEAN
        );
    """)


def create_user_city_relations(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_city_relations (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            city_id INTEGER REFERENCES cities(id),
            sub_period INTEGER,  -- Aggiunta dei campi interi
            notify_freq INTEGER  -- Aggiunta dei campi interi
        );
    """)

# Aggiunta del nuovo utente
def insert_user(user_name, chat_id, cur):
    cur.execute("SELECT id FROM users WHERE user_name = %s AND (chat_id = %s);", (user_name, chat_id))
    user_id = cur.fetchone()

    if not user_id:
        cur.execute("INSERT INTO users (user_name, chat_id) VALUES (%s, %s) RETURNING id;", (user_name, chat_id)) 
        user_id = cur.fetchone()

    return user_id[0] if user_id else None

#Aggiunta della nuova città
def insert_city(city, cur, tmp, feel_tmp, hum, weather, wind):
    cur.execute("""
        SELECT id 
        FROM cities 
        WHERE city_name = %s 
        AND (tmp = %s AND feel_tmp = %s AND hum = %s AND weather = %s AND wind = %s);
    """, (city, tmp, feel_tmp, hum, weather, wind))
    
    city_id = cur.fetchone()

    if not city_id:
        cur.execute("""
            INSERT INTO cities (city_name, tmp, feel_tmp, hum, weather, wind) 
            VALUES (%s, %s, %s, %s, %s, %s) 
            RETURNING id;
        """, (city, tmp, feel_tmp, hum, weather, wind))
        city_id = cur.fetchone()

    return city_id[0] if city_id else None

# Aggiunta della nuova sottoscrizione
def insert_user_city_relation(user_id, city_id, sub_period, notify_freq, cur):
    cur.execute("INSERT INTO user_city_relations (user_id, city_id, sub_period, notify_freq) VALUES (%s, %s, %s, %s);", 
                (user_id, city_id, sub_period, notify_freq))


