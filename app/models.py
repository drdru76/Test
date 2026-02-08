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
    STAGES = [
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
    ]

    STAGE_DETAILS = {
        '1_trigger': {
            'quote': '“Something important needs to be decided.”',
            'bullets': [
                'External trigger (opportunity, risk, deadline)',
                'Internal trigger (dissatisfaction, aspiration, fear of loss)',
                'Decision recognized as non-trivial (irreversible or high impact)'
            ],
            'risk': 'ignoring the decision or reacting emotionally'
        },
        '2_framing': {
            'quote': '“What exactly am I deciding?”',
            'bullets': [
                'Define the decision boundary (what is in vs out)',
                'Clarify time horizon (short vs long-term impact)',
                'Identify stakeholders (self, family, partners, shareholders)',
                'Key output: a clean decision statement',
                '“Should I do X instead of Y within Z timeframe, given constraints A & B?”'
            ],
            'risk': 'poorly framed decisions lead to wrong answers'
        },
        '3_objectives': {
            'quote': '“What does success look like?”',
            'bullets': [
                'Primary objective(s) (e.g., ROI, happiness, flexibility, legacy)',
                'Non-negotiable constraints (budget, legality, ethics, health, time)',
                'Trade-offs you are willing vs unwilling to make',
                'Tools: priority ranking, must-have vs nice-to-have'
            ],
            'risk': 'hidden constraints sabotage later stages'
        },
        '4_options': {
            'quote': '“What are my real options?”',
            'bullets': [
                'Obvious options (A vs B)',
                'Non-obvious options (delay, partial commit, hybrid, exit)',
                'Creative or asymmetric options',
                'Best practice: force at least 3–5 viable options'
            ],
            'risk': 'false dichotomies (“only two choices”)'
        },
        '5_information': {
            'quote': '“What do I need to know?”',
            'bullets': [
                'Facts, data, benchmarks',
                'Expert input',
                'First-hand validation (pilots, trials, site visits)',
                'Separate: What is known, What is assumed, What is unknowable'
            ],
            'risk': 'over-research or confirmation bias'
        },
        '6_evaluation': {
            'quote': '“Which option dominates under which conditions?”',
            'bullets': [
                'Pros/cons',
                'Financial models / scenarios',
                'Risk-reward asymmetry',
                'Best-case / worst-case analysis',
                'Reversibility vs irreversibility',
                'Common tools: Decision matrix, Expected value, Regret minimization, Pre-mortem analysis'
            ],
            'risk': 'analysis paralysis or false precision'
        },
        '7_emotions': {
            'quote': '“Can I live with this?”',
            'bullets': [
                'Gut reaction (not gut decision)',
                'Alignment with identity and long-term values',
                'Stress test: “How will I feel about this in 5–10 years?”',
                'Important: emotions are inputs, not noise'
            ],
            'risk': 'suppressing emotion or letting it dominate'
        },
        '8_commitment': {
            'quote': '“I choose.”',
            'bullets': [
                'Explicitly select one option',
                'Acknowledge uncertainty',
                'Accept trade-offs consciously',
                'High performers write this down: Why this option, Why not the others, What would change the decision later'
            ],
            'risk': 'half-decisions and hedging without clarity'
        },
        '9_execution': {
            'quote': '“How do I make this real?”',
            'bullets': [
                'First irreversible step',
                'Timeline & milestones',
                'Resource allocation',
                'Kill criteria (when to stop or pivot)'
            ],
            'risk': 'good decisions ruined by poor execution'
        },
        '10_review': {
            'quote': '“Was the decision good, given what was knowable?”',
            'bullets': [
                'Outcome vs process evaluation',
                'What signals to monitor',
                'Adjust or double-down',
                'Key distinction: A good decision can have a bad outcome—and vice versa.'
            ],
            'risk': 'ignoring the learning opportunity'
        }
    }

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140))
    deadline = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    status = db.Column(db.String(20), default='open') # open, closed
    stage = db.Column(db.String(40), default='1_trigger')
    category = db.Column(db.String(50))
    is_public = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # Content for each stage
    stage_1_trigger = db.Column(db.Text)
    stage_2_framing = db.Column(db.Text)
    stage_3_objectives = db.Column(db.Text)
    stage_4_options = db.Column(db.Text)
    stage_5_information = db.Column(db.Text)
    stage_6_evaluation = db.Column(db.Text)
    stage_7_emotions = db.Column(db.Text)
    stage_8_commitment = db.Column(db.Text)
    stage_9_execution = db.Column(db.Text)
    stage_10_review = db.Column(db.Text)

    options = db.relationship('Option', backref='decision', lazy='dynamic', cascade="all, delete-orphan")
    suggestions = db.relationship('Suggestion', backref='decision', lazy='dynamic', cascade="all, delete-orphan")
    clarifications = db.relationship('Clarification', backref='decision', lazy='dynamic', cascade="all, delete-orphan")
    stage_suggestions = db.relationship('StageSuggestion', backref='decision', lazy='dynamic', cascade="all, delete-orphan")

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
    action_type = db.Column(db.String(50)) # asked, read, clarification, suggestion, stage_suggestion
    decision_id = db.Column(db.Integer, db.ForeignKey('decision.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    user = db.relationship('User', backref='actions')
    decision = db.relationship('Decision', backref='actions')

    def __repr__(self):
        return f'<UserAction {self.action_type} by User {self.user_id} on Decision {self.decision_id}>'

class StageSuggestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stage_key = db.Column(db.String(40)) # e.g., '1_trigger'
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending') # pending, accepted, ignored
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    decision_id = db.Column(db.Integer, db.ForeignKey('decision.id'))
    
    author = db.relationship('User', backref='stage_suggestions')

    def __repr__(self):
        return f'<StageSuggestion {self.stage_key} for Decision {self.decision_id}>'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))
