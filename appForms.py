# DEFINE FORMS FOR THE APPLICATION WITH VALIDATION USING FLASK-WTF
from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, PasswordField, SubmitField)
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import InputRequired, Length, EqualTo, ValidationError
import re

# Form for Sign Up page
class SignUpForm(FlaskForm):
  # Username field
  username = StringField(label=('Username'), validators=[
    InputRequired('Username is required'),
    Length(min=1, max=20, message='Username can\'t be longer than 20 characters')
  ])

  # Description field
  description = TextAreaField(label=('Description'), validators=[
    InputRequired('Description is required'),
    Length(min=1, max=255, message='Description can\'t be longer than 255 characters')
  ])

  # Profile picture field
  profile_pic = FileField(label=('Profile pic (optional):'), validators=[
    FileAllowed(['jpg', 'jpeg', 'png'], 'Supported image files are .jpg, .jpeg and .png')
  ])

  # Password field
  password = PasswordField(label=('Password'), validators=[
    InputRequired('Password is required'),
    Length(min=8, max=15, message='Password must be between 8 and 15 characters'),
  ])

  # Password confirmation field
  confirmation = PasswordField(label=('Confirm your password'), validators=[
    InputRequired('Password confirmation is required'),
    Length(min=8, max=15, message='Password must be between 8 and 15 characters'),
    EqualTo('password', 'Password and confirmation must match')
  ])

  # Custom validators:
  # Function to validate username characters
  def validateUserChars(self, username):
    excluded = " ?!¿¡'^&/(){}[]=$#<>*"
    for char in excluded:
      if char in self.username.data:
        raise ValidationError(f'Character {char} is not allowed in username')

  # Function to validate password structure
  def validatePasswordStructure(self, password):
    # Check invalid characters
    excluded = " -+'\""
    for char in excluded:
      if char in self.password.data:
        raise ValidationError(f'Character {char} is not allowed in password')

    # Enforce password security
    pwLayout = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!#%*?&]{8,15}$")
    if not re.fullmatch(pwLayout, self.password.data):
      raise ValidationError("Password needs a lowercase and uppercase letter, a number and a special character")