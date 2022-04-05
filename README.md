# Distributed Systems Labs


## Setup

The .env file contains some customizable options.
Install requirements:

```bash
pip3 install -r requirements.txt
```

## Build

```bash
docker build -t ds_labs_server server -f server/Dockerfile && docker build -t ds_labs_frontend frontend -f frontend/Dockerfile
```

## Run

```bash
python3 labs.py <num-servers>
```

Once all services are started, the frontend should be reachable at the configured FRONTEND_PORT, e.g.: [localhost:8000](http://localhost:8000)