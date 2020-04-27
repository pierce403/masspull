import flask
from flask import render_template, request, Flask, g, send_from_directory
from werkzeug.utils import secure_filename

import json
import random
import os
from datetime import datetime
import glob

app = Flask(__name__,static_url_path='/static')
app.config['UPLOAD_FOLDER'] = 'uploads'
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

@app.route('/submit',methods=['GET', 'POST'])
def submit():
  if request.method == 'GET':
    return render_template("submit.html")
  else:
    if 'file' not in request.files:
      return "where's the file?"

    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
      return "was that a file?"
    if file:
      filename = secure_filename(file.filename)
      file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
      return "neat"

@app.route('/data/')
def data():
  thefiles = []
  #for file in os.listdir('data'):
  for net in range(1,255):
    matches = glob.glob('data/'+str(net)+'-*')
    if len(matches)==0:
      continue

    file=matches[0].split('/')[1]
    thedate = datetime.fromtimestamp(int(os.path.getmtime('data/'+file)))
    thesize = os.path.getsize('data/'+file)
    nicesize = thesize
    if thesize>1024:
      nicesize=str(round(thesize/1024,2))+"K"
    if thesize>(1024*1024):
      nicesize=str(round(thesize/(1024*1024),2))+"M"
    thelines = round(os.path.getsize('data/'+file)/36) # approx char/line in masscan data
    thefiles.append({'name':file,'date':thedate,'size':nicesize,'lines':thelines})
  return render_template("data.html",files=thefiles)

@app.route('/data/<path:filename>')
def assets(filename):
  # Add custom handling here.
  # Send a file download response.
  return send_from_directory('data', filename)
