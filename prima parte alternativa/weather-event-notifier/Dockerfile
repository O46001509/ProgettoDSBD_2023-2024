FROM python:3.8

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Espone la porta su cui il servizio ascolterà le richieste
EXPOSE 5001

# Comando per avviare il servizio
CMD ["python", "WeatherEventNotifier.py"]
