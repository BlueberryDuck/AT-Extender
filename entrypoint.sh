#!/bin/bash
set -e

# If env-vars set, write config.json into /config
if [ -n "${RUFNUMMER}" ] || [ -n "${PASSWORT}" ]; then
  cat > /config/config.json <<EOF
{
  "RUFNUMMER":    "${RUFNUMMER:-}",
  "PASSWORT":     "${PASSWORT:-}",
  "TELEGRAM":     "${TELEGRAM:-0}",
  "BOT_TOKEN":    "${BOT_TOKEN:-}",
  "CHAT_ID":      "${CHAT_ID:-}",
  "AUTO_UPDATE":  "${AUTO_UPDATE:-1}",
  "SLEEP_MODE":   "${SLEEP_MODE:-random}",
  "SLEEP_INTERVAL":"${SLEEP_INTERVAL:-70}",
  "BROWSER":      "${BROWSER:-chromium}"
}
EOF
fi

# Link config into the app folder
ln -sf /config/config.json /opt/at-extender/config.json

# Launch the bot
exec python /opt/at-extender/at-extender.py
