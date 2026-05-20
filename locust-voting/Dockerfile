FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY locustfile.py .

EXPOSE 8089

ENTRYPOINT ["locust"]
CMD ["-f", "/app/locustfile.py", "--web-host", "0.0.0.0"]
