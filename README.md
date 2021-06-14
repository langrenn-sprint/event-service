# event-service
Backend service to adminster events, will generate racelists etc


```
% curl -H "Content-Type: application/json" \
  -X POST \
  --data '{"username":"admin","password":"passw123"}' \
  http://localhost:8080/login
% export ACCESS="" #token from response
% curl -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -X POST \
  --data @tests/files/event.json \
  http://localhost:8080/events
% curl -H "Authorization: Bearer $ACCESS"  http://localhost:8080/events
```

## Running the API locally
Start the server locally:
```
% poetry run adev runserver -p 8080 src/event_service
```
## Running the API in a wsgi-server (gunicorn)
```
% cd src && poetry run gunicorn event_service:create_app --bind localhost:8080 --worker-class aiohttp.GunicornWebWorker
```
## Running the wsgi-server in Docker
To build and run the api in a Docker container:
```
% docker build -t digdir/event-service:latest .
% docker run --env-file .env -p 8080:8080 -d digdir/event-service:latest
```
The easier way would be with docker-compose:
```
docker-compose up --build
```
## Running tests
We use [pytest](https://docs.pytest.org/en/latest/) for contract testing.

To run linters, checkers and tests:
```
% nox
```
To run tests with logging, do:
```
% nox -s integration_tests -- --log-cli-level=DEBUG
```
## Environment variables
### `REDIS_HOST`
Hostname where the remote redis is reachable on default port (6379).
Default: localhost
### `REDIS_PASSWORD`
Password to the remote redis is reachable.
Default: `6379`
### `LOGGING_LEVEL`
One of the supported levels found [here](https://docs.python.org/3/library/logging.html#levels).
Default: `INFO`
### `CONFIG`
One of
- `dev`: will not use cache backend
- `test`: will not use cache backend
- `production`: will require and use a redis backend, cf docker-compose.yml
Default: `production`

An example .env file for local development without use of redis cache:
```
LOGGING_LEVEL=DEBUG
CONFIG=dev
```
