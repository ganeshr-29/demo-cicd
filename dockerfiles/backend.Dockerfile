FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY Application-Source-Code/app.py .
RUN useradd -m backend && chown -R backend:backend /app


USER backend
EXPOSE 5000
CMD ["python3", "/app/app.py"]

