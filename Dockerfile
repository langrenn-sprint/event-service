FROM python:3.12

RUN mkdir -p /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install "poetry==1.8.3"
COPY poetry.lock pyproject.toml /app/

# Project initialization:
RUN poetry config virtualenvs.create false \
  && poetry install --no-dev --no-interaction --no-ansi

ADD event_service /app/event_service

EXPOSE 8080

CMD gunicorn "event_service:create_app"  --config=event_service/gunicorn_config.py --worker-class aiohttp.GunicornWebWorker
