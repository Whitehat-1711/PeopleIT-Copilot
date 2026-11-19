.PHONY: help up down ingest test api ui all

help:
	@echo "WorkPulse AI - Management Commands"
	@echo "  make up      - Start Postgres & ChromaDB containers"
	@echo "  make down    - Stop all containers"
	@echo "  make ingest  - Embed and ingest policy documents into ChromaDB"
	@echo "  make test    - Run complete pytest test suite (43+ tests)"
	@echo "  make api     - Start FastAPI backend server on port 8001"
	@echo "  make ui      - Start Streamlit frontend on port 8501"

up:
	docker compose up -d postgres chromadb

down:
	docker compose down

ingest:
	cd backend && python -m backend.ingest

test:
	cd backend && pytest tests/ -v

api:
	cd backend && uvicorn backend.api:app --host 127.0.0.1 --port 8001 --reload

ui:
	streamlit run frontend/app.py --server.port 8501 --server.address 127.0.0.1
