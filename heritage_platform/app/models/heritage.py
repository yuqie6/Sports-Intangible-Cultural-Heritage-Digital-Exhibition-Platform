from app import db
from datetime import datetime

class HeritageItem(db.Model):
    __tablename__ = 'heritage_items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    cover_image = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    contents = db.relationship('Content', backref='heritage_item', lazy='dynamic')
    
    def __repr__(self):
        return f'<HeritageItem {self.name}>'
