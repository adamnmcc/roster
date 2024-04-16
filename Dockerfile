FROM python:3.11-slim

COPY requirements.txt ./

RUN pip3 install -r requirements.txt

WORKDIR /app

COPY *.py ./

COPY templates ./templates

CMD ["python3", "app.py"]
