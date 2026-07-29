up:
	@docker compose up -d --build

d:
	@docker compose down

build:
	@docker compose down
	@docker compose up -d --build