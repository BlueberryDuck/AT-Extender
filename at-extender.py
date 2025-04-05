import json
import time
import requests
import logging
import random
from playwright.sync_api import sync_playwright, TimeoutError

# Logging einrichten
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

LOGIN_URL = "https://login.alditalk-kundenbetreuung.de/signin/XUI/#login/"
DASHBOARD_URL = "https://www.alditalk-kundenportal.de/portal/auth/buchungsuebersicht/"
UBERSICHT_URL = "https://www.alditalk-kundenportal.de/portal/auth/uebersicht/"

VERSION = "1.0.2"  # Deine aktuelle Version

REMOTE_VERSION_URL = "https://raw.githubusercontent.com/Dinobeiser/AT-Extender/main/version.txt"  # Link zur Version
REMOTE_SCRIPT_URL = "https://raw.githubusercontent.com/Dinobeiser/AT-Extender/main/at-extender.py"  # Link zum neuesten Skript

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:137.0) Gecko/20100101 Firefox/137.0"
HEADLESS = True

# Konfiguration aus der config.json Datei laden
def load_config():
    with open("config.json", "r") as f:
        config = json.load(f)
    return config

# Konfigurationsvariablen aus der JSON-Datei laden
config = load_config()

RUFNUMMER = config["RUFNUMMER"]
PASSWORT = config["PASSWORT"]
BOT_TOKEN = config["BOT_TOKEN"]
CHAT_ID = config["CHAT_ID"]
AUTO_UPDATE = config["AUTO_UPDATE"]
TELEGRAM = config["TELEGRAM"]
SLEEP_MODE = config["SLEEP_MODE"]
SLEEP_INTERVAL = config["SLEEP_INTERVAL"]


TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def send_telegram_message(message, retries=3):
    if TELEGRAM == "1":
        for attempt in range(retries):
            try:
                response = requests.post(TELEGRAM_URL, data={"chat_id": CHAT_ID, "text": message})
                if response.status_code == 200:
                    logging.info("Telegram-Nachricht erfolgreich gesendet.")
                    return True
                else:
                    logging.warning(f"Fehler beim Senden (Versuch {attempt+1}): {response.text}")
            except Exception as e:
                logging.error(f"Fehler beim Telegram-Senden (Versuch {attempt+1}): {e}")
            time.sleep(2)
        logging.error("Telegram konnte nicht erreicht werden.")
        return False
    else:
        print("Keine Telegram Notify erwünscht")

# Funktion, um Versionen zu vergleichen (Versionen in Tupel umwandeln)
def compare_versions(local, remote):
    def to_tuple(v): return tuple(map(int, v.strip().split(".")))
    return to_tuple(remote) > to_tuple(local)

# Funktion, die auf Updates prüft
def check_for_update():
    if AUTO_UPDATE == "1":
        try:
            logging.info("🔍 Prüfe auf Updates...")

            # Abrufen der Versionsnummer von der URL
            response = requests.get(REMOTE_VERSION_URL)

            if response.status_code != 200:
                print(f"⚠️  Konnte Versionsinfo nicht abrufen, Statuscode: {response.status_code}")
                return

            # Extrahiere die Remote-Version und vergleiche sie mit der lokalen
            remote_version = response.text.strip()

            logging.info(f"🔍 Lokale Version: {VERSION} | Remote Version: {remote_version}")

            if compare_versions(VERSION, remote_version):
                logging.info(f"🚀 Neue Version verfügbar: {remote_version} (aktuell: {VERSION})")
                update = requests.get(REMOTE_SCRIPT_URL)
                if update.status_code == 200:
                    logging.info("✅ Update wird heruntergeladen...")
                    # Skript aktualisieren
                    script_path = os.path.realpath(sys.argv[0])
                    with open(script_path, 'w', encoding='utf-8') as f:
                        f.write(update.text)
                    logging.info("✅ Update erfolgreich! Starte neu...")
                    os.execv(sys.executable, ['python'] + sys.argv)
                else:
                    logging.info(f"❌ Fehler beim Herunterladen der neuen Version, Statuscode: {update.status_code}")
            else:
                logging.info("✅ Du verwendest die neueste Version.")
        except Exception as e:
            logging.info(f"❌ Fehler beim Update-Check: {e}")

    else:
        logging.info(f"Kein AutoUpdate erwünscht.")

def wait_and_click(page, selector, timeout=5000, retries=5):
    for attempt in range(retries):
        try:
            logging.info(f"Versuche, auf {selector} zu klicken (Versuch {attempt+1}/{retries})...")
            page.wait_for_selector(selector, timeout=timeout)
            page.click(selector)
            return True
        except TimeoutError:
            logging.warning(f"{selector} nicht gefunden. Neuer Versuch...")
            time.sleep(1)
    logging.error(f"Konnte {selector} nicht klicken.")
    return False

def login_and_check_data():
    with sync_playwright() as p:
        for attempt in range(3):  # 3 Versuche, falls Playwright abstürzt
            try:
                logging.info("Starte Browser...")
                browser = p.chromium.launch(headless=HEADLESS)
                context = browser.new_context(user_agent=USER_AGENT)
                page = context.new_page()

                logging.info("Öffne Aldi Talk Login-Seite...")
                page.goto(LOGIN_URL)
                page.wait_for_load_state("domcontentloaded")

                wait_and_click(page, 'button[data-testid="uc-deny-all-button"]')

                logging.info("Fülle Login-Daten aus...")
                page.fill('#input-2', RUFNUMMER)
                page.fill('#input-3', PASSWORT)

                if not wait_and_click(page, '[class="button button--solid button--medium button--color-default button--has-label"]'):
                    raise Exception("Login-Button konnte nicht geklickt werden.")

                logging.info("Warte auf Login...")
                time.sleep(8)

                logging.info("Öffne Datenvolumen-Übersicht...")
                page.goto(DASHBOARD_URL)
                page.wait_for_load_state("domcontentloaded")
                time.sleep(3)

                logging.info("Lese Datenvolumen aus...")
                GB_text = page.text_content('one-cluster[slot="help-text"]')

                if not GB_text:
                    raise Exception("Konnte das Datenvolumen nicht auslesen.")

                GB_text = GB_text.replace(" von 15 GB übrig im Inland", "").replace(",", ".")

                if "MB" in GB_text:
                    GB = float(GB_text.replace(" MB", "")) / 1024  # MB in GB umwandeln
                elif "GB" in GB_text:
                    GB = float(GB_text.replace(" GB", ""))
                else:
                    raise ValueError(f"Unerwartetes Format: {GB_text}")

                logging.info(f"Aktuelles Datenvolumen: {GB:.2f} GB")

                if GB < 1.0:
                    message = f"⚠️ Nur noch {GB:.2f} GB übrig! Versuche, Datenvolumen nachzubuchen..."
                    send_telegram_message(message)

                    logging.info("Öffne Nachbuchungsseite...")
                    page.goto(UBERSICHT_URL)
                    page.wait_for_load_state("domcontentloaded")
                    time.sleep(2)

                    logging.info("Klicke auf den Nachbuchungsbutton...")
                    if wait_and_click(page, 'one-button[slot="action"]'):
                        time.sleep(2)
                        send_telegram_message("✅ Datenvolumen erfolgreich nachgebucht!")
                        logging.info("1 GB Datenvolumen wurde nachgebucht!")
                    else:
                        raise Exception("❌ Konnte den Nachbuchungsbutton nicht klicken!")

                else:
                    send_telegram_message(f"✅ Noch {GB:.2f} GB übrig. Kein Nachbuchen erforderlich.")

                return  # Erfolgreicher Durchlauf, keine Wiederholung nötig

            except Exception as e:
                logging.error(f"Fehler im Versuch {attempt+1}: {e}")
                send_telegram_message(f"❌ Fehler beim Abrufen des Datenvolumens: {e}")

            finally:
                browser.close()
                logging.info("Browser geschlossen.")

            time.sleep(5)  # Kurze Pause zwischen Wiederholungen
        logging.error("Skript hat nach 3 Versuchen aufgegeben.")

def sleep_interval(config):
    mode = config.get("SLEEP_MODE", "random")  # "fixed" oder "random"

    if mode == "fixed":
        # Hole den Wert für das feste Intervall aus der config.json
        interval = config.get("SLEEP_INTERVAL", 70)  # Standard auf 70 Sekunden, wenn nicht gesetzt
        if interval < 60:
            print("⚠️ Intervall zu kurz, auf 90 Sekunden gesetzt.")
            interval = 90  # Mindestintervall von 90 Sekunden
    elif mode == "random":
        # Wenn SLEEP_MODE = random, dann zufälliger Wert zwischen 300 und 500 Sekunden
        interval = random.randint(300, 500)
    else:
        print("⚠️ Ungültiger SLEEP_MODE, verwende Standard 'random'.")
        interval = random.randint(300, 500)  # Standard zufälliger Wert zwischen 300 und 500 Sekunden

    logging.info(f"💤 Warte {interval} Sekunden...")
    time.sleep(interval)

if __name__ == "__main__":
    while True:
        check_for_update()  # Ruft die Update-Funktion auf
        logging.info("Starte neuen Durchlauf...")
        login_and_check_data()
        sleep_interval(config)
