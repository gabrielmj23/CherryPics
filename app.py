import os
import psycopg2
import appForms

from flask import Flask, request, render_template, redirect
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image

# Set up environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure application
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['WTF_CSRF_SECRET_KEY'] = os.getenv('SECRET_KEY')

# Connect app to database
dbConnection = psycopg2.connect(
  dbname = 'cherrypics',
  user = os.getenv('DB_USER'),
  password = os.getenv('DB_PASSWORD'),
  host = os.getenv('DB_HOST')
)
db = dbConnection.cursor()

# Stop responses from being cached
@app.after_request
def after_request(response):
  response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
  response.headers['Expires'] = 0
  response.headers['Pragma'] = 'no-cache'
  return response


# SIGN UP ROUTE
@app.route('/signup', methods=['GET', 'POST'])
def signup():
  form = appForms.SignUpForm()
  # User reached via GET -> Show sign up form
  if request.method == 'GET':
    return render_template('signup.html', form = form)

  # User reached via POST -> Validate form and save user in DB
  else:
    if form.validate_on_submit():
      # Validate username on database (UNIQUE)
      db.execute('SELECT * FROM users WHERE username = (%s)', (form.username.data,))
      dbConnection.commit()

      if db.rowcount < 1:
        # User with the same username was not found
        # Encrypt password
        encryptedPw = generate_password_hash(form.password.data)

        # Save profile picture file to static/users
        savedFileName = 'static/images/users/default.png'
        if form.profile_pic.data != None:
          # Resize profile picture
          profilePic = Image.open(form.profile_pic.data)
          profilePic.resize((200, 200))

          # Generate unique filename and save
          curDate = datetime.now()
          savedFileName = 'static/images/users/' + f'{curDate.day}-{curDate.month}-{curDate.year}_{curDate.hour}-{curDate.minute}-{curDate.second}_' + secure_filename(form.profile_pic.data.filename)
          profilePic.save(savedFileName, 'jpeg')
        
        # Save user in DB and redirect to login
        db.execute('INSERT INTO users (username, password, description, profile_pic) VALUES (%s, %s, %s, %s)',
          (form.username.data, form.description.data, encryptedPw, savedFileName + '.jpeg'))
        dbConnection.commit()
        
        redirect('/login')
      
      else:
        # Username is in use
        form.errors['db'] = ['Username is already in use']
    
        # Re-render
        return render_template('signup.html', form=form)
    
    # Base validation failed
    else:
      return render_template('signup.html', form=form)