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
        
    def to_dict(self, include_contents=False):
        """转换为字典用于API响应"""
        from app.models import User
        creator = User.query.get(self.created_by)
        
        result = {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'cover_image': self.cover_image,
            'created_by': self.created_by,
            'creator_name': creator.username if creator else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'content_count': self.contents.count()
        }
        
        if include_contents:
            from app.models import Content
            contents = Content.query.filter_by(heritage_id=self.id).order_by(Content.created_at.desc()).limit(10).all()
            result['recent_contents'] = [content.to_dict() for content in contents]
            
        return result
