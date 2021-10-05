# event-service
Backend service to create events, create raceclasses and assign bibs to contestants.

Supported [competition formats](https://assets.fis-ski.com/image/upload/v1624284540/fis-prod/assets/ICR_CrossCountry_2022_clean.pdf):

in this version:
- Interval Start competition,

In next version:
- Individual sprint competition without a qualification round.

In future versions:
- Mass start competition,
- Skiathlon competition,
- Pursuit,
- Individual sprint competition with a qualification round,
- Team sprint competition, and
- Relay competitions.

## Usage example
```
% curl -H "Content-Type: application/json" \
  -X POST \
  --data '{"username":"admin","password":"passw123"}' \
  http://localhost:8081/login
% export ACCESS="" #token from response
% curl -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS" \
  -X POST \
  --data @tests/files/event.json \
  http://localhost:8080/events
% curl -H "Authorization: Bearer $ACCESS"  http://localhost:8080/events
% curl -H "Content-Type: multipart/form-data" \
  -H "Authorization: Bearer $ACCESS" \
  -X POST \
  -F "data=@tests/files/allcontestants_eventid_364892.csv; type=text/csv" \
  http://localhost:8080/events/76083af9-8782-4d8a-882e-00ba7a0eaa55/contestants
% curl \
  -H "Authorization: Bearer $ACCESS" \
  -X GET \
  http://localhost:8080/events/e734d3b5-31c0-4c39-8215-c6ad10c1fa5c/contestants
```
Look to the [openAPI specification](./specification.yaml) for the details.

## Running the API locally
Start the server locally:
```
% poetry run adev runserver -p 8080 --aux-port 8089 src/event_service
```
## Running the API in a wsgi-server (gunicorn)
```
% cd src && poetry run gunicorn event_service:create_app --bind localhost:8080 --worker-class aiohttp.GunicornWebWorker
```
## Running the wsgi-server in Docker
To build and run the api in a Docker container:
```
% docker build -t gcr.io/langrenn-sprint/event-service:latest .
% docker run --env-file .env -p 8080:8080 -d gcr.io/langrenn-sprint/event-service:latest
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
To run specific test:
```
% nox -s integration_tests -- -k test_create_event_adapter_fails
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
