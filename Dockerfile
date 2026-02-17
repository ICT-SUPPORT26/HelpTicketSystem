FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# system deps for some python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# copy and install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# copy app
COPY . /app

# ensure uploads directory exists
RUN mkdir -p /app/uploads

EXPOSE 5000

# run with gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "main:app", "--workers", "2"]
