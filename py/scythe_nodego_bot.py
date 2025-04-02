import requests
import time
import os
import logging
import json

# ---------------- Configuration Constants ----------------
TASKS_FILE = 'tasks.csv'       # CSV file with task credentials (username, bearer_token)
POLL_INTERVAL = 120            # Polling interval in seconds

# ---------------- Logging Setup ----------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ---------------- API Endpoints ----------------
api_url = 'https://nodego.ai/api/user/me'  # NodeGo API endpoint

# ---------------- Load Tasks from CSV ----------------
def read_tasks(filename=TASKS_FILE):
    tasks = []
    try:
        with open(filename, newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)  # Skip the first row if it's a header
            
            for row in reader:
                if len(row) < 3:  # Ensure the row has all required columns
                    continue
                
                username, bearer_token, _ = row  # Skip proxy for now
                if not username.strip() or not bearer_token.strip():
                    continue
                
                tasks.append({
                    "username": username.strip(),
                    "bearer_token": bearer_token.strip(),
                })
    except FileNotFoundError:
        logging.error(f"Tasks file '{filename}' not found.")
    except Exception as e:
        logging.error(f"Error reading tasks from CSV: {e}")
    return tasks

# ---------------- Send Ping to NodeGo ----------------
def send_ping(token):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'Referer': 'https://nodego.ai/',
        'Origin': 'https://nodego.ai/'
    }

    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            logging.info(f"[✔] Ping exitoso para {token[:6]}...")
        else:
            logging.error(f"[✖] Error en ping para {token[:6]}: {response.status_code}")
    except requests.RequestException as e:
        logging.error(f"[✖] Fallo en la solicitud de ping: {e}")

# ---------------- Main Bot Function ----------------
def start_bot():
    tasks_list = read_tasks()

    if not tasks_list:
        logging.error("No tasks to process. Exiting.")
        return
    
    logging.info("[🔥] Iniciando ScytheBot para NodeGo...\n")
    while True:
        logging.info(f"\n⏰ Ping Cycle at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        for task in tasks_list:
            send_ping(task["bearer_token"])
            time.sleep(POLL_INTERVAL)  # Espera el intervalo entre pings

if __name__ == "__main__":
    start_bot()
