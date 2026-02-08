from datetime import datetime
from app import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    
    # Profile fields
    headline = db.Column(db.String(140))
    about = db.Column(db.Text)
    location = db.Column(db.String(64))
    experience = db.Column(db.Text)
    education = db.Column(db.Text)
    skills = db.Column(db.String(255))
    
    decisions = db.relationship('Decision', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Decision(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140))
    description = db.Column(db.Text)
    deadline = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    status = db.Column(db.String(20), default='open') # open, closed
    category = db.Column(db.String(50))
    is_public = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    options = db.relationship('Option', backref='decision', lazy='dynamic', cascade="all, delete-orphan")
    suggestions = db.relationship('Suggestion', backref='decision', lazy='dynamic', cascade="all, delete-orphan")
    clarifications = db.relationship('Clarification', backref='decision', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Decision {self.title}>'

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140))
    description = db.Column(db.Text)
    pros = db.Column(db.Text)
    cons = db.Column(db.Text)
    decision_id = db.Column(db.Integer, db.ForeignKey('decision.id'))

    def __repr__(self):
        return f'<Option {self.title}>'

class Suggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140))
    description = db.Column(db.Text)
    pros = db.Column(db.Text)
    cons = db.Column(db.Text)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending') # pending, accepted, ignored
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    decision_id = db.Column(db.Integer, db.ForeignKey('decision.id'))
    
    author = db.relationship('User', backref='suggestions')

    def __repr__(self):
        return f'<Suggestion {self.title}>'

class Clarification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending') # pending, ignored
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    decision_id = db.Column(db.Integer, db.ForeignKey('decision.id'))

    author = db.relationship('User', backref='clarifications')

    def __repr__(self):
        return f'<Clarification {self.message[:20]}>'

class UserAction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    action_type = db.Column(db.String(50)) # asked, read, clarification, suggestion
    decision_id = db.Column(db.Integer, db.ForeignKey('decision.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    user = db.relationship('User', backref='actions')
    decision = db.relationship('Decision', backref='actions')

    def __repr__(self):
        return f'<UserAction {self.action_type} by User {self.user_id} on Decision {self.decision_id}>'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
