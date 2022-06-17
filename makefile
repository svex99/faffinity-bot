# Development options

build:
	docker image build -t faffinity-bot-dev .

init-db:
	docker container run -it --rm \
		-v $(PWD)/data:/app/data \
		faffinity-bot-dev \
		python3 cmd/init_db.py

run:
	docker container run -it --rm \
		--name fa-bot-dev \
		-v $(PWD)/data:/app/data \
		-v $(PWD)/src:/app/src \
		--env-file data/.env \
		faffinity-bot-dev

# Production options

build-prod:
	docker image build \
		-f Dockerfile.production \
		-t svex/faffinity-bot .

init-db-prod:
	docker container run -it --rm \
		-v $PWD/data:/app/data \
		svex/faffinity-bot \
		python3 cmd/init_db.py

run-prod:
	docker container run -it --rm \
	--name fa-bot \
	--restart always \
	-v $PWD/data:/app/data \
	svex/faffinity-bot
