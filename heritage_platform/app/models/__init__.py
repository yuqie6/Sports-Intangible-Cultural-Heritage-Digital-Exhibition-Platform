# 导入所有模型，确保它们在SQLAlchemy创建会话时被正确注册

from . import user
from . import heritage
from . import content
from . import interaction

# 为方便使用，导出主要模型类
from .user import User
from .heritage import HeritageItem
from .content import Content
from .interaction import Comment, Like, Favorite
