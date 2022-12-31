from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home(): # where is server defined !!
  return 'miobo!!!!!!'#this is the part that displays text omtd

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()