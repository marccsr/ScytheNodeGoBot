import requests
import time
import os

# Configuración
data_file = 'data.txt'
proxies_file = 'proxies.txt'
api_url = 'https://nodego.ai/api/'
ping_interval = 15  # segundos

# Cargar tokens de `data.txt`
def load_tokens():
    if not os.path.exists(data_file):
        print("[✖] No se encontró el archivo data.txt")
        return []
    
    with open(data_file, 'r') as f:
        return [line.strip() for line in f if line.strip()]

# Cargar proxies de `proxies.txt` (opcional)
def load_proxies():
    if not os.path.exists(proxies_file):
        return []
    
    with open(proxies_file, 'r') as f:
        return [line.strip() for line in f if line.strip()]

# Enviar ping a NodeGo
def send_ping(token, proxy=None):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-GB,en;q=0.9,es-ES;q=0.8,es;q=0.7',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'Referer': 'https://nodego.ai/',
        'Origin': 'https://nodego.ai/'
    }
    
    proxies = {'http': proxy, 'https': proxy} if proxy else None
    
    try:
        response = requests.get(api_url, headers=headers, proxies=proxies, timeout=10)
        if response.status_code == 200:
            print(f"[✔] Ping exitoso para {token[:6]}...")
        else:
            print(f"[✖] Error en ping para {token[:6]}: {response.status_code}")
    except requests.RequestException as e:
        print(f"[✖] Fallo en la solicitud de ping: {e}")

# Ejecutar el bot
def start_bot():
    tokens = load_tokens()
    proxies = load_proxies()
    
    if not tokens:
        print("[✖] No hay tokens para usar.")
        return
    
    print("\n[🔥] Iniciando ScytheBot para NodeGo...\n")
    while True:
        print(f"\n⏰ Ping Cycle at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        for i, token in enumerate(tokens):
            proxy = proxies[i % len(proxies)] if proxies else None
            send_ping(token, proxy)
        print(f"\n⌛ Esperando {ping_interval} segundos antes del próximo ciclo...")
        time.sleep(ping_interval)

if __name__ == "__main__":
    start_bot()
