from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, DateTimeField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Length, Optional, ValidationError, Email

class DecisionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=140)])
    description = TextAreaField('Description', validators=[Length(max=65535)])
    deadline = DateTimeField('Deadline (YYYY-MM-DD HH:MM:SS)', format='%Y-%m-%d %H:%M:%S', validators=[Optional()])
    is_public = BooleanField('Make Public', default=True)
    submit = SubmitField('Submit')

class OptionForm(FlaskForm):
    title = StringField('Option Title', validators=[DataRequired(), Length(min=1, max=140)])
    description = TextAreaField('Description', validators=[Length(max=65535)])
    pros = TextAreaField('Pros', validators=[Length(max=65535)])
    cons = TextAreaField('Cons', validators=[Length(max=65535)])
    submit = SubmitField('Add Option')

class SuggestionForm(FlaskForm):
    title = StringField('Suggestion Title', validators=[DataRequired(), Length(min=1, max=140)])
    description = TextAreaField('Description', validators=[Length(max=65535)])
    pros = TextAreaField('Pros', validators=[Length(max=65535)])
    cons = TextAreaField('Cons', validators=[Length(max=65535)])
    submit = SubmitField('Submit Suggestion')

class ClarificationForm(FlaskForm):
    message = TextAreaField('What needs clarification?', validators=[DataRequired(), Length(min=5, max=65535)])
    submit = SubmitField('Request Clarification')

class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    is_admin = BooleanField('Is Admin')
    headline = StringField('Headline', validators=[Length(max=140)])
    about = TextAreaField('About Me', validators=[Length(max=65535)])
    location = StringField('Location', validators=[Length(max=64)])
    experience = TextAreaField('Experience', validators=[Length(max=65535)])
    education = TextAreaField('Education', validators=[Length(max=65535)])
    skills = StringField('Skills (comma separated)', validators=[Length(max=255)])
    submit = SubmitField('Save Profile')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            from app.models import User
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')
