FROM python:3.8

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

# Comando di avvio
CMD ["python", "Handle_notifier.py"]


