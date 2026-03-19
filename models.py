from datetime import datetime
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from extensions import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_confirmed  = db.Column(db.Boolean, default=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    scans = db.relationship('Scan', backref='user', lazy=True, cascade='all, delete-orphan')

    def get_confirmation_token(self):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps(self.email, salt='email-confirm')

    def get_reset_token(self):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return s.dumps(self.email, salt='password-reset')

    @staticmethod
    def verify_confirmation_token(token, max_age=3600):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = s.loads(token, salt='email-confirm', max_age=max_age)
        except Exception:
            return None
        return User.query.filter_by(email=email).first()

    @staticmethod
    def verify_reset_token(token, max_age=1800):
        s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = s.loads(token, salt='password-reset', max_age=max_age)
        except Exception:
            return None
        return User.query.filter_by(email=email).first()

    def total_scans(self):
        return len(self.scans)

    def most_detected_disease(self):
        if not self.scans:
            return 'No scans yet'
        from collections import Counter
        counts = Counter(s.disease for s in self.scans)
        return counts.most_common(1)[0][0]

    def __repr__(self):
        return f'<User {self.email}>'


class Scan(db.Model):
    __tablename__ = 'scans'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    disease     = db.Column(db.String(100), nullable=False)
    confidence  = db.Column(db.Float, nullable=False)
    severity    = db.Column(db.String(20), nullable=False)
    crop        = db.Column(db.String(50), nullable=False)
    note        = db.Column(db.String(300), nullable=True)
    image_name  = db.Column(db.String(200), nullable=True)
    scanned_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def crop_from_disease(self):
        d = self.disease.lower()
        if 'corn' in d:   return 'Corn'
        if 'pepper' in d: return 'Pepper'
        if 'potato' in d: return 'Potato'
        if 'tomato' in d: return 'Tomato'
        return 'Unknown'

    def to_dict(self):
        return {
            'id':         self.id,
            'disease':    self.disease,
            'confidence': self.confidence,
            'severity':   self.severity,
            'crop':       self.crop,
            'note':       self.note or '',
            'scanned_at': self.scanned_at.strftime('%d %b %Y, %H:%M'),
        }

    def __repr__(self):
        return f'<Scan {self.disease} {self.confidence:.1f}%>'