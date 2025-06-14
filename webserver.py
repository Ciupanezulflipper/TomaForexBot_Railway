# webserver.py
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running.'

@app.route('/healthz')
def health():
    return 'OK'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
