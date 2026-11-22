
FROM python:3.13-slim

WORKDIR /app

# Python-Abhängigkeiten installieren
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Bot-Code kopieren
COPY *.py ./

# Datenverzeichnis vorbereiten
RUN mkdir -p /app/data

# Python-Ausgabe direkt in Docker-Logs schreiben
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
