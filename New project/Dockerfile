FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

COPY requirements.txt requirements.txt
COPY requirements-lstm.txt requirements-lstm.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-lstm.txt

COPY . .

EXPOSE 5000

CMD ["waitress-serve", "--listen=0.0.0.0:5000", "app:app"]
