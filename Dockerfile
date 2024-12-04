FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive

WORKDIR /code

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    netcat-openbsd \
    curl \
    gcc \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /code/
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /code/logs /code/staticfiles /code/media
RUN chmod 777 /code/logs /code/staticfiles /code/media

COPY . /code/

# Debug commands
RUN ls -la /code/
RUN pwd
RUN cat /code/entrypoint.sh || echo "entrypoint.sh not found"

RUN chmod +x /code/entrypoint.sh || echo "Failed to chmod entrypoint.sh"

# Add test script
COPY test_smart_hotel.py /code/

EXPOSE 8000

ENTRYPOINT ["/code/entrypoint.sh"]