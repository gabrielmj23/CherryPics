from http.client import HTTPException
import os
import psycopg2
import appForms
import secrets

from flask import Flask, request, render_template, redirect, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from PIL import Image

from loginRequired import loginRequired

# Set up environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure application
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['WTF_CSRF_SECRET_KEY'] = os.getenv('SECRET_KEY')

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

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


# INDEX ROUTE
@app.route('/', methods=['GET'])
@loginRequired
def index():
  # Get posts from database
  db.execute('SELECT id, description, image, like_count, posted_on FROM posts ORDER BY posted_on DESC')
  dbConnection.commit()
  posts = db.fetchall()

  # If there are posts, select five or less at random for carousel
  carouselPosts = []
  if len(posts) > 0:
    carouselPosts = secrets.SystemRandom().sample(posts, min(5, len(posts)))

  # Render index page
  return render_template('index.html', carouselPosts = carouselPosts, posts = posts)


# TOGGLE LIKE ROUTE
@app.route('/posts/<int:postId>/likes', methods=['POST'])
@loginRequired
def toggleLike(postId):
  # Get like status from request
  likeStatus = request.form.get('liked')

  # Get post like count
  db.execute('SELECT like_count FROM posts WHERE id = (%s)', (postId,))
  dbConnection.commit()
  postLikeCount = db.fetchone()[0]

  # User hasn't liked post -> Add like to database and update post like count
  if likeStatus == 'False':
    # Insert new like into DB
    db.execute('INSERT INTO likes (user_id, post_id) VALUES (%s, %s)', (session['user_id'], postId))
    dbConnection.commit()

    # Update post like count and reload page
    db.execute('UPDATE posts SET like_count = (%s) WHERE id = (%s)', (postLikeCount + 1, postId))
    dbConnection.commit()
    return redirect(f'/posts/{postId}')
  
  # User has liked post -> Delete like from database and update post like count
  else:
    # Delete like from DB
    db.execute('DELETE FROM likes WHERE user_id = (%s) AND post_id = (%s)', (session['user_id'], postId))
    dbConnection.commit()

    # Update post like count and reload page
    db.execute('UPDATE posts SET like_count = (%s) WHERE id = (%s)', (postLikeCount - 1, postId))
    dbConnection.commit()
    return redirect(f'/posts/{postId}')


# DELETE COMMENT ROUTE
@app.route('/posts/<int:postId>/comments/<int:commentId>/delete', methods=['POST'])
@loginRequired
def deleteComment(postId, commentId):
  # Delete comment from DB
  db.execute('DELETE FROM comments WHERE id = (%s)', (commentId,))
  dbConnection.commit()

  # Reload page
  return redirect(f'/posts/{postId}')


# ADD COMMENT ROUTE
@app.route('/posts/<int:postId>/comments', methods=['POST'])
@loginRequired
def addComment(postId):
  # Insert comment into DB
  curDate = datetime.now()
  db.execute('INSERT INTO comments (author_id, post_id, content, posted_on) VALUES (%s, %s, %s, %s)',
    (session['user_id'], postId, request.form.get('content'), curDate))
  dbConnection.commit()

  # Reload post page
  return redirect(f'/posts/{postId}')


# DELETE USER ROUTE
@app.route('/users/<int:userId>/delete', methods=['POST'])
@loginRequired
def deleteUser(userId):  
  # Get all posts from user and save id's and images
  db.execute('SELECT id, image FROM posts WHERE author_id = (%s)', (userId,))
  dbConnection.commit()
  postList = db.fetchall()

  # Delete comments and likes from deleted posts
  for postTuple in postList:
    db.execute('DELETE FROM comments WHERE post_id = (%s)', (postTuple[0],))
    db.execute('DELETE FROM likes WHERE post_id = (%s)', (postTuple[0],))
    # Delete post image
    os.remove(os.path.join(os.getcwd(), postTuple[1]))
  dbConnection.commit()

  # Update like count from posts where user has left a like
  db.execute('UPDATE posts AS p SET like_count = like_count - 1 WHERE p.id IN (SELECT post_id FROM likes WHERE user_id = (%s) AND post_id = p.id)', (userId,))

  # Delete comments and likes from user
  db.execute('DELETE FROM comments WHERE author_id = (%s)', (userId,))
  db.execute('DELETE FROM likes WHERE user_id = (%s)', (userId,))
  dbConnection.commit()

  # Delete all posts from user
  db.execute('DELETE FROM posts WHERE author_id = (%s)', (userId,))
  dbConnection.commit()

  # Delete user from DB and profile pic from server
  db.execute('DELETE FROM users WHERE id = (%s) RETURNING profile_pic', (userId,))
  dbConnection.commit()
  userPfp = db.fetchone()
  os.remove(os.path.join(os.getcwd(), userPfp[0]))

  # Clear session and redirect to sign up page
  session.clear()
  return redirect('/signup')


# VIEW USER ROUTE
@app.route('/users/<int:userId>', methods=['GET'])
@loginRequired
def viewUser(userId):
  # Get user from database
  db.execute('SELECT id, username, description, profile_pic FROM users WHERE id = (%s)', (userId,))
  dbConnection.commit()
  urlUser = db.fetchone()

  # Show error page if user doesn't exist
  if urlUser is None:
    return render_template('error.html', errorMsg = 'User not found')

  # Get user's posts, if exists
  userPosts = []
  db.execute('SELECT id, description, image, posted_on, like_count FROM posts WHERE author_id = (%s)', (urlUser[0],))
  dbConnection.commit()
  userPosts = db.fetchall()
  
  # Render user page template
  return render_template('userview.html', user = urlUser, posts = userPosts)


# DELETE POST ROUTE
@app.route('/posts/<int:postId>/delete', methods=['POST'])
@loginRequired
def deletePost(postId):
  # Delete from DB comments and likes corresponding to that post
  db.execute('DELETE FROM comments WHERE post_id = (%s)', (postId,))
  db.execute('DELETE FROM likes WHERE post_id = (%s)', (postId,))
  dbConnection.commit()

  # Delete post from DB
  db.execute('DELETE FROM posts WHERE id = (%s) RETURNING image', (postId,))
  dbConnection.commit()

  # Delete image from server
  postImage = db.fetchone()
  os.remove(os.path.join(os.getcwd(), postImage[0]))

  # Redirect to index page
  return redirect('/')


# VIEW POST ROUTE
@app.route('/posts/<int:postId>', methods=['GET'])
@loginRequired
def viewPost(postId):
  # Get post from database (if it doesn't exist, it'll be None)
  db.execute('SELECT u.id, u.username, p.id, p.description, p.image, p.posted_on, p.like_count FROM posts AS p INNER JOIN users AS u ON p.author_id = u.id WHERE (p.id) = (%s)', (postId,))
  dbConnection.commit()
  urlPost = db.fetchone()

  # Show error page if post not found
  if urlPost is None:
    return render_template('error.html', errorMsg = 'Post not found')
  
  # Get comments from post if exists
  postComments = []
  userLikes = None
  db.execute('SELECT c.id, u.id, u.username, c.content, c.posted_on FROM comments AS c INNER JOIN users AS u ON c.author_id = u.id WHERE (c.post_id) = (%s)', (postId,))
  dbConnection.commit()
  postComments = db.fetchall()
    
  # Additionally, check if user likes post
  db.execute('SELECT * FROM likes WHERE user_id = (%s) AND post_id = (%s)', (session['user_id'], postId))
  dbConnection.commit()
  userLikes = db.fetchone()
  if userLikes is None:
    userLikes = False
  else:
    userLikes = True

  # Show post view page
  return render_template('postview.html', post = urlPost, comments = postComments, liked = userLikes)


# NEW POST ROUTE
@app.route('/new', methods=['GET', 'POST'])
@loginRequired
def newPost():
  form = appForms.NewPostForm()
  # User reached via GET -> Show new post form
  if request.method == 'GET':
    return render_template('newpost.html', form = form)
  
  # User reached via POST -> Validate and save post in DB
  else:
    if form.validate_on_submit():
      # Resize post image
      postImage = Image.open(form.image.data)
      postImage.thumbnail((800, 800))

      # Generate unique filename and save
      curDate = datetime.now()
      savedFileName = 'static/images/posts/' + f'{curDate.day}-{curDate.month}-{curDate.year}_{curDate.hour}-{curDate.minute}-{curDate.second}_' + secure_filename(form.image.data.filename)
      postImage.save(savedFileName, 'png')

      # Save post in DB
      db.execute('INSERT INTO posts (author_id, description, image, posted_on, like_count) VALUES (%s, %s, %s, %s, %s) RETURNING (id)',
        (session['user_id'], form.description.data, savedFileName, curDate, 0))
      dbConnection.commit()

      # Send to post page
      return redirect(f'/posts/{db.fetchone()[0]}')
    
    # Failed basic validation
    else:
      return render_template('newpost.html', form = form)


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
          (form.username.data, encryptedPw, form.description.data, savedFileName))
        dbConnection.commit()
        
        return redirect('/login')
      
      else:
        # Username is in use
        form.errors['db'] = ['Username is already in use']
    
        # Re-render
        return render_template('signup.html', form=form)
    
    # Base validation failed
    else:
      return render_template('signup.html', form=form)


# LOG IN ROUTE
@app.route('/login', methods=['GET', 'POST'])
def login():
  form = appForms.LogInForm()
  # User reached via GET -> Show log in form
  if request.method == 'GET':
    return render_template('login.html', form = form)
  
  # User reached via POST -> Validate log in information
  else:
    if form.validate_on_submit():
      # Find username match in DB
      db.execute('SELECT * FROM users WHERE username = (%s)', (form.username.data,))
      dbConnection.commit()
      foundUser = db.fetchone()
      
      # Check for login errors
      if foundUser == None or not check_password_hash(foundUser[2], request.form.get("password")):
        form.errors['db'] = ['Wrong username/password']
        return render_template('login.html', form = form)

      # If valid, save user session and send to home page
      else:
        session['user_id'] = foundUser[0]
        return redirect('/')

    # Basic validation failed
    else:
      return render_template('login.html', form=form)


# LOG OUT ROUTE
@app.route('/logout', methods=['GET'])
def logout():
  # Clear session and redirect to login page
  session.clear()
  return redirect('/login')


# ERROR WATCHING
def errorhandler(e):
  if not isinstance(e, HTTPException):
    e = InternalServerError()
  return render_template('error.html', errorMsg = e)

for code in default_exceptions:
  app.errorhandler(code)(errorhandler)