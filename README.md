# CherryPics
## Video demo:
https://youtu.be/F5rrlQknb1I

## Description:
CherryPics is an image-sharing website/social media, meant for photographers to share their latest works, be displayed on the front page and get likes and opinions from other users.

The web app is quite simple in the things it handles. You can create and delete users, posts, comments and likes for posts. These functionalities are implemented with forms on the frontend and Flask routes on the backend.

For future plans, I'd like to add the ability to update user information, post descriptions and comments, as well as adding a follow and notification system. It would also be interesting to make the Flask app only for backend using proper HTTP verbs like PUT and DELETE, and develop the frontend separately using a framework like React. It's also a challenge to make the website properly responsive, adjusting image sizes to different screens.

## Technologies:
- Flask
- Jinja
- HTML, CSS and Bootstrap
- Flask-WTF (Used for form validation)
- Pillow (Used for image handling)
- PostgreSQL and Psycopg2 (Database and ORM)

## File overview:
### [main.py](main.py)
Main Flask application file, initiates database connection and then declares all the routes with their corresponding methods. These routes usually make some database queries according to the user's requirement, and then render a template with the received data or redirect to a different route.

### [loginRequired.py](loginRequired.py)
Helper file that declares a function that decorates protected routes, meant to only be accessed when logged in. It simply checks the session dictionary for a user id, and is adapted from the CS50 finance project.

### [appForms.py](appForms.py)
File used to declare the sign up, log in and new post forms as classes using Flask-WTF, making it possible to easily validate user's inputs and show error messages.

### [Templates folder](templates/)
Contains all the Jinja templates made for this web app, rendered after each request. The structure is quite similar, and they make heavy use of Bootstrap classes and components for things like list groups and carousels.

### [Static folder](static/)
Contains a small custom stylesheet and an 'images' folder, that contains icons, user profile pictures and post images. There's a default profile picture, for cases when the user doesn't wish to provide one.

## Design choices/history:
Originally, the project was intended to be made in JavaScript, using NodeJS and Express for the backend, and React for the frontend. I actually got pretty far, the backend was pretty much done. However, there were issues handling image uploads from frontend to backend, and this being a key part of the project, was slowing it down significantly.

After a couple of days of hard work on this issue, I decided to postpone that version of the project, and come back to the Flask framework seen in the course, with Jinja templates over React for the frontend.

I went with PostgreSQL over SQLite for the database, due to the first one being a bit more popular and demanded, it's an important skill I believe.