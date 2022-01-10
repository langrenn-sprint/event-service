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

```Shell
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
  http://localhost:8080/events/<event-id/contestants
% curl \
  -H "Authorization: Bearer $ACCESS" \
  -X GET \
  http://localhost:8080/events/<event-id>/contestants
```

Look to the [openAPI specification](./specification.yaml) for the details.

## Running the API locally

Start the server locally:

```Shell
% poetry run adev runserver -p 8080 --aux-port 8089 event_service
```

## Running the API in a wsgi-server (gunicorn)

```Shell
% poetry run gunicorn event_service:create_app --bind localhost:8080 --worker-class aiohttp.GunicornWebWorker
```

## Running the wsgi-server in Docker

To build and run the api in a Docker container:

```Shell
% docker build -t ghcr.io/langrenn-sprint/event-service:latest .
% docker run --env-file .env -p 8080:8080 -d ghcr.io/langrenn-sprint/event-service:latest
```

The easier way would be with docker-compose:

```Shell
docker-compose up --build
```

## Running tests

We use [pytest](https://docs.pytest.org/en/latest/) for contract testing.

To run linters, checkers and tests:

```Shell
% nox
```

To run specific test:

```Shell
% nox -s integration_tests -- -k test_create_event_adapter_fails
```

To run tests with logging, do:

```Shell
% nox -s integration_tests -- --log-cli-level=DEBUG
```

## Environment variables

An example .env file for local development:

```Shell
JWT_SECRET=secret
JWT_EXP_DELTA_SECONDS=3600
ADMIN_USERNAME=admin
ADMIN_PASSWORD=password
USERS_HOST_SERVER=localhost
USERS_HOST_PORT=8086
DB_USER=event-service
DB_PASSWORD=password
LOGGING_LEVEL=DEBUG
```
