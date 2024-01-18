FROM python:3.8

# Imposto il work directory nell'app
WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Comando di avvio
CMD ["python", "Consumer.py"]


