# scripts

A collection of simple scripts to load the database via the event_service API.

```
% poetry shell
% python load_competition_formats.py
```

You will need at least this in your .env to run it locally against the containers in this project:
```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=passw123
EVENTS_HOST_SERVER=localhost
EVENTS_HOST_PORT=8080
USERS_HOST_SERVER=localhost
USERS_HOST_PORT=8081
DB_USER=event-service
DB_PASSWORD=password
```
