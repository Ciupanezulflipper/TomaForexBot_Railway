from flask import Flask
import os
import asyncio
from cloudbot import run_bot_loop  # make sure this function exists in cloudbot.py

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running.'

@app.route('/healthz')
def health():
    return 'OK'

@app.before_first_request
def start_background_task():
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot_loop())  # run your bot in background

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
