FROM python:3.9-slim

WORKDIR /app

RUN pip install gunicorn==20.1.0

COPY requirements.txt ./

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

RUN chmod +x run_app.sh

ENTRYPOINT ["/app/run_app.sh"]