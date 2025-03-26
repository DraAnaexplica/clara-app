import os
import sqlite3
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from claraprompt import prompt_clara, prompt_proactive
import pytz
import schedule
import time
import threading

app = Flask(__name__)

tz = pytz.timezone('America/Sao_Paulo')

def init_db():
    conn = sqlite3.connect('chat_history.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sender TEXT,
                  message TEXT,
                  timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

def get_current_time():
    return datetime.now(tz).strftime('%H:%