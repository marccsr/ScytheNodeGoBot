import aiohttp
import asyncio
import time
import os
import logging
import csv
from aiohttp import ClientSession, TCPConnector
import socket

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
                
                username, bearer_token, proxy = row  # Proxy column is optional
                if not username.strip() or not bearer_token.strip():
                    continue
                
                tasks.append({
                    "username": username.strip(),
                    "bearer_token": bearer_token.strip(),
                    "proxy": proxy.strip() if len(row) > 2 else None  # Optional proxy field
                })
    except FileNotFoundError:
        logging.error(f"Tasks file '{filename}' not found.")
    except Exception as e:
        logging.error(f"Error reading tasks from CSV: {e}")
    return tasks

# ---------------- Send Ping to NodeGo ----------------
async def send_ping(session, token, proxy=None):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'Referer': 'https://nodego.ai/',
        'Origin': 'https://nodego.ai/'
    }

    # Handle proxies with authentication
    connector = None
    if proxy:
        connector = await create_proxy_connector(proxy)
    
    try:
        async with session.get(api_url, headers=headers, connector=connector) as response:
            if response.status == 200:
                logging.info(f"[✔] Ping exitoso para {token[:6]}...")
            else:
                logging.error(f"[✖] Error en ping para {token[:6]}: {response.status}")
    except Exception as e:
        logging.error(f"[✖] Fallo en la solicitud de ping: {e}")

# ---------------- Create Proxy Connector ----------------
async def create_proxy_connector(proxy):
    """Create aiohttp connector using proxy with authentication"""
    try:
        # Parse proxy URL (http://username:password@ip:port)
        proxy_url = proxy.strip().lower()
        if not proxy_url.startswith("http"):
            proxy_url = "http://" + proxy_url

        # Parse the proxy URL to extract username, password, and URL
        parsed_url = aiohttp.helpers.urllib.parse.urlparse(proxy_url)
        proxy_host = parsed_url.hostname
        proxy_port = parsed_url.port
        proxy_user = parsed_url.username
        proxy_password = parsed_url.password

        # Setup proxy with authentication
        proxy_connector = TCPConnector(ssl=False)
        return aiohttp.ClientSession(connector=proxy_connector, proxy=proxy_url, auth=aiohttp.BasicAuth(proxy_user, proxy_password))
    
    except Exception as e:
        logging.error(f"[✖] Error al crear el conector de proxy: {e}")
        return None

# ---------------- Main Bot Function ----------------
async def start_bot():
    tasks_list = read_tasks()

    if not tasks_list:
        logging.error("No tasks to process. Exiting.")
        return

    async with aiohttp.ClientSession() as session:
        logging.info("[🔥] Iniciando ScytheBot para NodeGo...\n")
        while True:
            logging.info(f"\n⏰ Ping Cycle at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            for task in tasks_list:
                proxy = task.get("proxy")
                await send_ping(session, task["bearer_token"], proxy)
                await asyncio.sleep(POLL_INTERVAL)  # Espera el intervalo entre pings

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_bot())
