
FROM python:3.11-slim

WORKDIR /app
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ------------------------------
# 7. Environment variables
#    (these can also be set from docker-compose)
# ------------------------------
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# ------------------------------
# 8. Expose service port
# ------------------------------
EXPOSE 5001

# ------------------------------
# 9. Run the Flask application
# ------------------------------
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]
