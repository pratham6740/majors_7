from datetime import datetime
from flaskblog import db, login_manager
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(40), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.username}' , '{self.email}' , '{self.image_file}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    branch = db.Column(db.String(100), nullable=False)
    verdict = db.Column(db.String(20), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    interview_date = db.Column(db.String(20), nullable=True)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(100), nullable=False)
    round = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "branch": self.branch,
            "verdict": self.verdict,
            "type": self.type,
            "interview_date": self.interview_date,
            "date_posted": self.date_posted.isoformat(),
            "content": self.content,
            "role": self.role,
            "round": self.round,
            "user_id": self.user_id,
            # Add any other fields you need here
        }
    
    def __repr__(self):
        return f"Post('{self.title}' , '{self.date_posted}')"