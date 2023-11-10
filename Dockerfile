FROM python:3.10.12-buster

RUN pip install poetry==1.7.0
RUN poetry config virtualenvs.create false

WORKDIR /app

COPY poetry.lock pyproject.toml .
RUN poetry install --no-interaction --no-ansi

COPY . .

CMD ["poetry", "run", "bot"]
