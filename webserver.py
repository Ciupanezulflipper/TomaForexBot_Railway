from flask import Flask
import os
import asyncio
import threading
from cloudbot import run_bot_loop  # must be an async function

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running.'

@app.route('/healthz')
def health():
    return 'OK'

def start_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot_loop())

@app.before_first_request
def launch_background():
    thread = threading.Thread(target=start_async_loop)
    thread.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
