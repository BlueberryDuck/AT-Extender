#!/bin/bash
set -e

# If environment variables are set, write them into /config/config.json
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

# Symlink or copy the config into the app folder
ln -sf /config/config.json /opt/at-extender/config.json

# Exec your bot (so signals are forwarded correctly)
exec python /opt/at-extender/at-extender.py
