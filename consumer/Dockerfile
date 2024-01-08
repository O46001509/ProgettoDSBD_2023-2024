# Usa un'immagine di Python
FROM python:3.8

# Imposta il work directory nell'app
WORKDIR /app

# Copia il file requirements.txt nella directory dell'app
COPY requirements.txt .

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Copia il contenuto dell'app nell'immagine
COPY . /app

# Comando di avvio
CMD ["python", "Consumer.py"]


