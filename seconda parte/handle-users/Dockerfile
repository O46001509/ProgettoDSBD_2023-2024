FROM python:3.8

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Comando per avviare il servizio
CMD ["python", "App.py"]