run:
	uvicorn app.main:app --reload
db:
	docker compose up -d