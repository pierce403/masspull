import flask
from flask import render_template, request, Flask, g, send_from_directory

import json
import random
import os

app = Flask(__name__,static_url_path='/static')
app.jinja_env.add_extension('jinja2.ext.do')

@app.route('/')
def landing():
  return render_template("index.html")

@app.route('/getwork')
def getwork():
  work = {}
  work['type']='masscan'
  work['target']=random.randint(1,255); # be smarter some day
  return json.dumps(work)

@app.route('/submit')
def submit():
  return render_template("submit.html")

@app.route('/data/')
def data():
  return render_template("data.html",files=os.listdir('data'))

@app.route('/data/<path:filename>')
def assets(filename):
  # Add custom handling here.
  # Send a file download response.
  return send_from_directory('data', filename)
