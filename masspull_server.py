import flask
from flask import render_template, request, Flask, g, send_from_directory, abort, jsonify
#from flask_sqlalchemy import SQLAlchemy
#from sqlalchemy import Table, Column, Float, Integer, String, MetaData, ForeignKey
from werkzeug.utils import secure_filename

import json
import random
import string
import os
import time

from web3.auto import w3
from eth_account.messages import defunct_hash_message

from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, set_access_cookies, jwt_optional, get_raw_jwt, unset_jwt_cookies

from ethhelper import *

app = Flask(__name__,static_url_path='/static')
app.jinja_env.add_extension('jinja2.ext.do')

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

@app.route('/data/<path:filename>')
def assets(filename):
  # Add custom handling here.
  # Send a file download response.
  return send_from_directory('data', filename)

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

