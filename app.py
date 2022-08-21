import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Set up environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure application
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Connect app to database
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY')

# Stop responses from being cached
@app.after_request
def after_request(response):
  response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
  response.headers['Expires'] = 0
  response.headers['Pragma'] = 'no-cache'
  return response
