# 体育非遗数字展示平台

连接课堂学习与数字化分享，促进体育非遗文化的传播与保护。

## 环境要求与配置

### 环境需求

- Python 3.9 或更高版本
- MySQL 数据库服务

### 主要依赖包

- Flask 及其扩展 (Flask-Login, Flask-SQLAlchemy, Flask-WTF, Flask-Migrate)
- PyMySQL - MySQL数据库连接
- Pillow - 图像处理
- email_validator - 邮箱验证

完整依赖列表可在 `requirements.txt` 文件中查看。

### 数据库配置

可以通过环境变量或 `config.py` 配置数据库连接：

- `DB_USER`: 数据库用户名（默认: root）
- `DB_PASSWORD`: 数据库密码
- `DB_HOST`: 数据库主机（默认: localhost）
- `DB_NAME`: 数据库名称（默认: heritage_platform）

## 快速开始

1. **初始化数据库**
   - 运行 `初始化数据库.bat`
   - 这会创建必要的数据库表和初始用户

2. **启动应用**
   - 运行 `启动应用.bat`
   - 应用将在 http://127.0.0.1:5000 启动

## 默认用户

- 管理员：username: `admin`, password: `adminpassword`
- 教师：username: `teacher`, password: `teacherpassword`
- 学生：username: `student`, password: `studentpassword`

## 项目结构

```
heritage_platform/
├── app/                     # 应用主目录
│   ├── models/             # 数据模型
│   ├── routes/             # 路由控制
│   ├── templates/          # HTML模板
│   ├── static/             # 静态文件
│   ├── forms/             # 表单类
│   └── utils/             # 工具函数
├── config.py               # 配置文件
├── run.py                 # 启动脚本
└── init_db.py             # 数据库初始化
```

## 项目功能

- **用户系统**: 支持学生、教师和管理员角色
- **非遗项目管理**: 展示和管理体育类非遗项目
- **内容管理**: 发布文章、视频等多媒体内容
- **交流论坛**: 用户间交流讨论的社区
- **互动功能**: 评论、点赞、收藏等功能

## 故障排除指南

### 1. 数据库连接错误
   - 确保 MySQL 服务已启动
   - 检查 `config.py` 中的数据库连接信息是否正确
   - 确保数据库用户有足够的权限

### 2. 500 服务器错误
   - 查看控制台输出的错误日志
   - 检查数据库查询或模板渲染错误
   - 确保所需的表和字段都存在

### 3. 文件上传问题
   - 确保 `static/uploads` 目录有写入权限
   - 检查上传文件大小是否超过限制（默认16MB）
   - 确认上传文件类型是否被允许
   
### 4. 环境变量设置
可通过以下环境变量自定义配置：
   - `SECRET_KEY`: 应用密钥
   - `FLASK_CONFIG`: 运行环境（development/production）
   - `DB_*`: 数据库相关配置
   - `LOG_LEVEL`: 日志级别

## 开发指南

项目使用 Flask 框架开发，采用蓝图结构组织代码。开发新功能时，请遵循以下步骤：

1. 在 models/ 中定义数据模型
2. 在 forms/ 中创建相关表单
3. 在 routes/ 中实现路由逻辑
4. 在 templates/ 中创建页面模板

### 代码规范

- 使用4空格缩进
- 函数和方法添加文档字符串
- 使用类型提示增加代码可读性
- 遵循 PEP 8 编码规范

### 测试

在提交代码前：
1. 确保所有新功能都有适当的错误处理
2. 验证数据库操作的事务完整性
3. 检查模板中的变量是否都已定义
4. 验证用户权限控制是否正确
