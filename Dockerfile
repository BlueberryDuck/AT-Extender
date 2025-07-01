FROM python:3.9-slim

# 1. Install system deps & Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
      curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/at-extender

# 2. Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install

# 3. Copy application code into the image
COPY . /opt/at-extender

# 4. Declare a mount point for config.json
VOLUME ["/config"]

# 5. Entrypoint script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
