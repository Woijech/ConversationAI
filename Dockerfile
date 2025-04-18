FROM python:3.12

WORKDIR /app

COPY requirements.txt .

RUN pip install -r app/requirements.txt

COPY . .

CMD ["python", "-m", "app.main"]