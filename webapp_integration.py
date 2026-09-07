import asyncio
from aiohttp import web
import aiohttp_cors
import json
import os
import subprocess
import threading
import time
import re
import logging

USER_DATA = {}
WEBAPP_URL = "https://localhost:8080"

def run_tunnel():
    global WEBAPP_URL
    while True:
        logging.info("Starting localhost.run SSH tunnel...")
        proc = subprocess.Popen(
            ['ssh', '-R', '80:localhost:8080', '-o', 'StrictHostKeyChecking=no', 'nokey@localhost.run'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        for line in iter(proc.stdout.readline, ''):
            match = re.search(r'https://[a-zA-Z0-9.-]+\.lhr\.life', line)
            if match:
                WEBAPP_URL = match.group(0)
                logging.info(f"New Tunnel URL: {WEBAPP_URL}")
        proc.wait()
        logging.warning("Tunnel closed. Restarting in 3s...")
        time.sleep(3)

async def index(request):
    return web.FileResponse('templates/index.html')

async def get_data(request):
    session_id = request.query.get('session_id')
    if not session_id or session_id not in USER_DATA:
        return web.json_response({"error": "No data found"}, status=404)
    return web.json_response(USER_DATA[session_id])

async def start_webapp():
    app = web.Application()
    app.router.add_get('/', index)
    app.router.add_get('/api/data', get_data)
    
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(allow_credentials=True, expose_headers="*", allow_headers="*")
    })
    for route in list(app.router.routes()):
        cors.add(route)
        
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logging.info("WebApp running on port 8080")
