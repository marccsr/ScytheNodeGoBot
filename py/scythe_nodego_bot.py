import aiohttp
import asyncio
import time
import os
import logging
import json
import csv

TASKS_FILE = 'tasks.csv'
POLL_INTERVAL = 120
LOGIN_URL = 'https://nodego.ai/api/auth/login'
PING_URL = 'https://nodego.ai/api/user/nodes/ping'

WEBSITE_KEY = '0x4AAAAAAA4zgfgCoYChIZf4'
CAPTCHA_API_KEY = 'ff5b51608b309ac7cb673197d74033b0'
CREATE_TASK_URL = 'https://api.2captcha.com/createTask'
GET_TASK_RESULT_URL = 'https://api.2captcha.com/getTaskResult'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ---------------- Read and Save Tasks ----------------
def read_tasks(filename=TASKS_FILE):
    tasks = []
    try:
        with open(filename, newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)
            
            for row in reader:
                if len(row) < 4:
                    continue
                
                username, password, proxy, bearer_token = row
                if not username.strip() or not password.strip():
                    continue
                
                tasks.append({
                    "username": username.strip(),
                    "password": password.strip(),
                    "proxy": proxy.strip() if proxy else None,
                    "bearer_token": bearer_token.strip() if bearer_token else None
                })
    except FileNotFoundError:
        logging.error(f"Tasks file '{filename}' not found.")
    except Exception as e:
        logging.error(f"Error reading tasks from CSV: {e}")
    return tasks

def save_tasks(tasks, filename=TASKS_FILE):
    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['username', 'password', 'proxy', 'bearer_token'])
            for task in tasks:
                writer.writerow([task['username'], task['password'], task.get('proxy', ''), task.get('bearer_token', '')])
        logging.info(f"Tasks successfully saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving tasks to CSV: {e}")

def create_proxy_dict(proxy):
    if proxy:
        proxy_parts = proxy.split('@')
        if len(proxy_parts) == 2:
            user_pass, url = proxy_parts
            username, password = user_pass.split(':')
            return {
                'http': f'http://{username}:{password}@{url}',
                'https': f'http://{username}:{password}@{url}'
            }
    return None

# ---------------- Solve Captcha ----------------
async def solve_turnstile_captcha():
    create_task_payload = {
        "clientKey": CAPTCHA_API_KEY,
        "task": {
            "type": "TurnstileTaskProxyless",
            "websiteURL": "https://app.nodego.ai/",
            "websiteKey": WEBSITE_KEY
        }
    }
    
    try:
        logging.info("Creating captcha task in 2captcha...")
        async with aiohttp.ClientSession() as session:
            create_response = await session.post(CREATE_TASK_URL, json=create_task_payload)
            create_data = await create_response.json()
        
        if create_data.get('errorId') != 0:
            logging.error(f"Error creating captcha task: {create_data.get('errorCode')} - {create_data.get('errorDescription')}")
            return None
        
        task_id = create_data.get('taskId')
        if not task_id:
            logging.error("Could not get taskId from 2captcha")
            return None
        
        logging.info(f"Captcha task created successfully: taskId={task_id}")
        
        get_result_payload = {
            "clientKey": CAPTCHA_API_KEY,
            "taskId": task_id
        }
        
        max_attempts = 24
        for attempt in range(1, max_attempts + 1):
            logging.info(f"Attempt {attempt}/{max_attempts} to get captcha result...")
            
            await asyncio.sleep(5)
            
            result_response = await aiohttp.ClientSession().post(GET_TASK_RESULT_URL, json=get_result_payload)
            result_data = await result_response.json()
            
            if result_data.get('status') == 'ready':
                token = result_data.get('solution', {}).get('token')
                if token:
                    logging.info(f"Captcha solved successfully: {token[:30]}...")
                    return token
            
            if result_data.get('errorId') != 0:
                logging.error(f"Error solving captcha: {result_data.get('errorCode')} - {result_data.get('errorDescription')}")
                break
            
            logging.info("Captcha still processing, waiting...")
        
        logging.error("Timeout waiting to solve captcha")
        return None
    except Exception as e:
        logging.error(f"Error solving captcha: {e}")
        return None

# ---------------- Login ----------------
async def login(username, password, captcha_token=None):
    try:
        headers = {
            'Host': 'nodego.ai',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
        }
        
        if captcha_token:
            payload = {
                "captcha": captcha_token,
                "email": username,
                "password": password
            }
            logging.info(f"Login for user: {username} with captcha: {captcha_token[:30]}...")
        else:
            payload = {
                "email": username,
                "password": password
            }
            logging.info(f"Attempting direct login for {username}...")
        
        async with aiohttp.ClientSession() as session:
            response = await session.post(LOGIN_URL, headers=headers, json=payload)
        
        if response.status == 201:
            data = await response.json()
            access_token = data.get('metadata', {}).get('accessToken')
            if access_token:
                logging.info(f"Successful login for {username}")
                return access_token
            else:
                logging.error(f"Token not found in response for {username}")
        else:
            logging.error(f"Login failed for {username}: {response.status}")
        
        return None
    except Exception as e:
        logging.error(f"Error in login request: {e}")
        return None

# ---------------- Ping ----------------
async def send_ping(session, token, proxy=None):
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/json',
    }

    proxies = create_proxy_dict(proxy)
    
    try:
        async with session.post(PING_URL, headers=headers, json={"type": "extension", "extensionInstalled": True}, proxy=proxies) as response:
            if response.status == 200:
                logging.info(f"Successful ping for {token[:6]}... Status: {response.status}")
                return True
            return False
    except aiohttp.ClientError as e:
        logging.error(f"Error in ping request: {e}")
        return False

# ---------------- Main Bot Function ----------------
async def start_bot():
    tasks_list = read_tasks()

    if not tasks_list:
        logging.error("No tasks to process. Exiting.")
        return
    
    logging.info("Starting ScytheBot for NodeGo...\n")
    
    tasks_updated = False
    for i, task in enumerate(tasks_list):
        username = task["username"]
        password = task["password"]
        bearer_token = task.get("bearer_token", "")
        
        if bearer_token:
            logging.info(f"Using existing valid bearer token for {username}")
            continue
        
        logging.info(f"Attempting direct login for {username}")
        fresh_token = await login(username, password)
        
        if not fresh_token:
            logging.info(f"Direct login failed, trying with captcha for {username}")
            captcha_token = await solve_turnstile_captcha()
            if captcha_token:
                fresh_token = await login(username, password, captcha_token)
        
        if fresh_token:
            tasks_list[i]["bearer_token"] = fresh_token
            tasks_updated = True
            
    if tasks_updated:
        save_tasks(tasks_list)
    
    async with aiohttp.ClientSession() as session:
        while True:
            logging.info(f"\nPing cycle at {time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            for task in tasks_list:
                bearer_token = await send_ping(session, bearer_token, task.get("proxy", None))
                await asyncio.sleep(5)
                
            logging.info(f"Waiting {POLL_INTERVAL} seconds for next cycle...")
            await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    asyncio.run(start_bot())

