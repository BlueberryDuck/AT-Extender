# Use a specific Playwright Python image (Ubuntu 22.04 “jammy”) 
FROM mcr.microsoft.com/playwright/python:v1.53.0-jammy

WORKDIR /opt/at-extender

# 1) Install any extra Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Copy application code into the image
COPY . /opt/at-extender

# 3) Declare a mount point for config.json
VOLUME ["/config"]

# 4) Entrypoint script
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["entrypoint.sh"]
