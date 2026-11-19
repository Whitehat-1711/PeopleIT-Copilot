FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY frontend/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend/ /app/frontend/
COPY data/ /app/data/

EXPOSE 8501

ENV BACKEND_API_URL=http://backend:8001

CMD ["streamlit", "run", "frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
