include .env
export

.PHONY: help create build backend run down remove create-gcp build-gcp backend-gcp run-gcp down-gcp remove-gcp build-ingest push-ingest

help:
	@sed -ne '/@sed/!s/## //p' $(MAKEFILE_LIST)

create:		## create docker volumes and network
	docker volume create bitcoin-pipeline-redpanda
	docker volume create bitcoin-pipeline-data
	docker volume create bitcoin-pipeline-airflow-postgres
	docker volume create bitcoin-pipeline-postgres
	docker network create bitcoin-pipeline-network
build:		## docker compose build
	docker compose -f docker-compose.yaml --profile app build --no-cache
backend:	## docker compose up backend
	docker compose -f docker-compose.yaml up -d
run:		## docker compose up backend and app
	docker compose -f docker-compose.yaml up -d
# 	docker compose -f docker-compose.yaml up websocket-producer -d
# 	docker exec flink-jobmanager flink run -py /opt/flink/jobs/run_postgres.py
# 	docker compose -f docker-compose.yaml up dash-app -d
down:		## docker compose down backend and app
	docker compose -f docker-compose.yaml --profile app down
clean:		## remove all images and rebuild from scratch
	docker rmi -f airflow_base spark_master spark_worker 2>/dev/null || true
	docker compose -f docker-compose.yaml --profile app build
remove:		## remove docker volumes and network. remove will delete stored data
	@echo -n "Are you sure you want to remove stored data? [y/N] " && read ans && [ $${ans:-N} = y ]
# 	docker volume remove bitcoin-pipeline-redpanda
	docker volume remove bitcoin-pipeline-data
	docker volume remove bitcoin-pipeline-airflow-postgres
	docker volume remove bitcoin-pipeline-postgres
	docker network remove bitcoin-pipeline-network