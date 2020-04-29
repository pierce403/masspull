import flask
from flask import render_template, request, Flask, g, send_from_directory, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table, Column, Float, Integer, String, DateTime, MetaData, ForeignKey, func
from werkzeug.utils import secure_filename

import json
import random
import string
import os
import time
from datetime import datetime
import glob

from web3.auto import w3
from eth_account.messages import defunct_hash_message

from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, set_access_cookies, jwt_optional, get_raw_jwt, unset_jwt_cookies

from ethhelper import *

app = Flask(__name__,static_url_path='/static')
app.jinja_env.add_extension('jinja2.ext.do')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uploads.db'
db = SQLAlchemy(app)

# Setup the Flask-JWT-Extended extension
# log2(26^22) ~= 100 (pull at least 100 bits of entropy)
app.config['JWT_SECRET_KEY'] = ''.join(random.choice(string.ascii_lowercase) for i in range(22))
#app.config['JWT_SECRET_KEY'] = '12345'
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
#app.config['JWT_COOKIE_SECURE'] = True # TODO MAKE SURE THIS IS TRUE!!
#app.config['JWT_ACCESS_COOKIE_PATH'] = '/api/'
app.config['JWT_COOKIE_CSRF_PROTECT'] = True
app.config['JWT_CSRF_CHECK_FORM'] = True
jwt = JWTManager(app)

app.config['UPLOAD_FOLDER'] = 'uploads'

@app.before_first_request
def setup():
  print("[+] running setup")
  try:
    db.create_all()
    print("[+] created uploads db")
  except:
    print("[+] uploads db already exists")

# schema to track uploaded files
class Upload(db.Model):
  user = db.Column(db.String(80))
  status = db.Column(db.String(80))
  filename = db.Column(db.String(80), primary_key=True, nullable=False, unique=True)
  filesize = db.Column(Integer, default=0)
  lines = db.Column(Integer, default=0)
  ctime = db.Column(DateTime, default=func.now())

# schema to track votes
class Votes(db.Model):
  filename = db.Column(db.String(80), primary_key=True, nullable=False, unique=True)
  user = db.Column(db.String(80), primary_key=True, nullable=False)
  support = db.Column(Integer)
  ctime = db.Column(DateTime, default=func.now())

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
@jwt_optional
def upload():
  if request.method == 'GET':
    return render_template("submit.html",csrf_token=(get_raw_jwt() or {}).get("csrf"))
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

      current_user = get_jwt_identity()

      db.session.add(Upload(user=current_user,filename=filename,status="NEW"))
      db.session.commit()
      #numtokens = tokencount(current_user)
      #if numtokens > 100:
      #  msg="The Galaxy is on Orion's Belt"
      #else:
      #  msg="You need more than 100 GST to view this message."
      return ("HELLO "+str(current_user))

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

@app.route('/uploads/')
def uploads():
  thefiles = []
  #for file in os.listdir('data'):
  for upload in Upload.query.all(): # TODO maybe limit by date at some point?
    print("FOUND "+upload.filename)
    thedate = str(upload.ctime)
    #thedate = datetime.fromtimestamp(upload.ctime)
    thesize = upload.filesize
    nicesize = thesize
    if thesize>1024:
      nicesize=str(round(thesize/1024,2))+"K"
    if thesize>(1024*1024):
      nicesize=str(round(thesize/(1024*1024),2))+"M"
    thefiles.append({'name':upload.filename,'date':thedate,'size':nicesize,'lines':upload.lines})

  return render_template("uploads.html",files=thefiles)


@app.route('/data/<path:filename>')
def data_files(filename):
  # Add custom handling here.
  # Send a file download response.
  return send_from_directory('data', filename)

@app.route('/uploads/<path:filename>')
def upload_files(filename):
  # Add custom handling here.
  # Send a file download response.
  return send_from_directory('uploads', filename)

# custom hook to ensure user gets logged out if jwt fails
@jwt.invalid_token_loader
def invalid_token_loader(msg):
  resp = jsonify({'msg': msg})
  unset_jwt_cookies(resp) # this usually doesn't happen for some reason
  return resp,200

# custom hook to ensure user gets logged out if jwt fails
@jwt.expired_token_loader
def expired_token_loader(msg):
  resp = jsonify({'msg': 'Token has expired'})
  unset_jwt_cookies(resp) # this usually doesn't happen for some reason
  return resp,401
@app.route('/secret')
@jwt_required
def secret():
  current_user = get_jwt_identity()
  numtokens = tokencount(current_user)
  if numtokens > 100:
    msg="The Galaxy is on Orion's Belt"
  else:
    msg="You need more than 100 GST to view this message."
  return ("HELLO "+str(current_user)+" "+msg)

@app.route('/login', methods=['POST'])
def login():

    print("[+] creating session")

    print("info: "+(str(request.json)))

    public_address = request.json[0]
    signature = request.json[1]

    #domain = "masspull.org"
    domain = "127.0.0.1"

    rightnow = int(time.time())
    sortanow = rightnow-rightnow%600

    original_message = 'Signing in to {} at {}'.format(domain,sortanow)
    print("[+] checking: "+original_message)
    message_hash = defunct_hash_message(text=original_message)
    signer = w3.eth.account.recoverHash(message_hash, signature=signature)
    print("[+] fascinating")

    if signer == public_address:
      print("[+] this is fine "+str(signer))
       # account.nonce = account.generate_nonce()
       # db.session.commit()
    else:
        abort(401, 'could not authenticate signature')

    print("[+] OMG looks good")

    access_token = create_access_token(identity=public_address)

    resp = jsonify({'login': True})
    set_access_cookies(resp, access_token)
    return resp, 200

