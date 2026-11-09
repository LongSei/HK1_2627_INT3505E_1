FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY run.py .
EXPOSE 5000
CMD python -c "from app import create_app; create_app()" && gunicorn -b 0.0.0.0:5000 -w 2 run:app
