from app import db
from . import beijing_time

class HeritageItem(db.Model):
    """非物质文化遗产项目模型
    
    此模型存储非遗项目的基本信息，是平台的核心数据实体之一。
    每个非遗项目可以关联多个内容（文章、图片、视频等），由用户（通常是教师角色）创建。
    """
    __tablename__ = 'heritage_items'  # 指定数据库表名
    
    # 基本字段
    id = db.Column(db.Integer, primary_key=True)  # 主键ID
    name = db.Column(db.String(100), nullable=False)  # 非遗项目名称，不允许为空
    category = db.Column(db.String(50), nullable=False)  # 项目分类，如"民间音乐"、"传统技艺"等
    description = db.Column(db.Text)  # 项目详细描述，存储长文本
    cover_image = db.Column(db.String(255))  # 封面图片路径
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))  # 创建者ID，外键关联users表
    created_at = db.Column(db.DateTime, default=beijing_time)  # 创建时间，默认使用北京时间
    
    # 关系定义
    contents = db.relationship('Content', back_populates='heritage', lazy=True)  # 与内容模型的一对多关系
    
    def __repr__(self):
        """模型的字符串表示
        
        Returns:
            str: 模型的简短表示，用于调试和日志输出
        """
        return f'<HeritageItem {self.name}>'
        
    def to_dict(self, include_contents=False):
        """转换为字典格式，用于API响应
        
        将模型实例转换为字典格式，便于序列化为JSON响应。
        可选择是否包含关联的内容数据。
        
        Args:
            include_contents (bool): 是否包含关联的内容数据，默认为False
            
        Returns:
            dict: 包含模型数据的字典
        """
        from app.models import User
        # 获取创建者信息
        creator = User.query.get(self.created_by)
        
        # 构建基本数据字典
        result = {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'cover_image': self.cover_image,
            'created_by': self.created_by,
            'creator_name': creator.username if creator else None,  # 创建者用户名
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),  # 格式化创建时间
            'content_count': self.contents.count()  # 关联内容数量
        }
        
        # 如果需要包含内容数据，则查询最近的10条内容
        if include_contents:
            from app.models import Content
            contents = Content.query.filter_by(heritage_id=self.id).order_by(Content.created_at.desc()).limit(10).all()
            result['recent_contents'] = [content.to_dict() for content in contents]  # 将内容模型也转换为字典
            
        return result
