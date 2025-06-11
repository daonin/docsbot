FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN pip install supervisor
COPY supervisord.conf ./
CMD ["supervisord", "-c", "/app/supervisord.conf"] 