from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, DateTimeField, IntegerField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Optional, ValidationError, Email

class DecisionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=140)])
    deadline = DateTimeField('Deadline (YYYY-MM-DD HH:MM:SS)', format='%Y-%m-%d %H:%M:%S', validators=[Optional()])
    stage = SelectField('Current Stage', choices=[
        ('1_trigger', '1. Trigger / Awareness'),
        ('2_framing', '2. Framing the Decision'),
        ('3_objectives', '3. Objective & Constraint Definition'),
        ('4_options', '4. Option Generation'),
        ('5_information', '5. Information Gathering & Validation'),
        ('6_evaluation', '6. Evaluation & Modeling'),
        ('7_emotions', '7. Emotional & Values Check'),
        ('8_commitment', '8. Commitment Decision'),
        ('9_execution', '9. Execution Planning'),
        ('10_review', '10. Review & Adaptation')
    ])
    is_public = BooleanField('Make Public', default=True)
    
    # Stage-specific content fields
    stage_1_trigger = TextAreaField('1. Trigger / Awareness Content')
    stage_2_framing = TextAreaField('2. Framing Content')
    stage_3_objectives = TextAreaField('3. Objective & Constraint Content')
    stage_4_options = TextAreaField('4. Option Generation Content')
    stage_5_information = TextAreaField('5. Information Gathering Content')
    stage_6_evaluation = TextAreaField('6. Evaluation & Modeling Content')
    stage_7_emotions = TextAreaField('7. Emotional & Values Content')
    stage_8_commitment = TextAreaField('8. Commitment Content')
    stage_9_execution = TextAreaField('9. Execution Content')
    stage_10_review = TextAreaField('10. Review & Adaptation Content')

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
