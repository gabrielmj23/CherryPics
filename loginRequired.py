from flask import session, redirect
from functools import wraps

# Function to validate login status for protected routes
def loginRequired(f):
  @wraps(f)
  def decoratedFunc(*args, **kwargs):
    if session.get('user_id') is None:
      return redirect('/login')
    return f(*args, **kwargs)
  return decoratedFunc