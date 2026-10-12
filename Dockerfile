FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends --only-upgrade liblzma5 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /portal

COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt
    
RUN groupadd --gid 10001 portal \
    && useradd --uid 10001 --gid portal --create-home portal

COPY app/ ./app/
COPY run.py seed.py ./

RUN mkdir -p /portal/instance \
    && chown portal:portal /portal/instance

USER portal

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "app:create_app()"]
