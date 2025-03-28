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
- Markdown - 文本格式转换支持

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

3. **重置数据库**（如果需要）
   - 运行 `重置数据库.bat`
   - 此操作会清空并重新初始化数据库

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
│   ├── api/               # API接口
│   └── utils/             # 工具函数
├── migrations/            # 数据库迁移文件
├── logs/                  # 日志文件目录
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
- **通知系统**: 用户互动、内容更新等通知
- **Markdown支持**: 文章内容支持Markdown格式，增强排版效果
- **内容权限管理**: 用户可以管理自己创建的内容，包括删除功能

## 使用指南

详细的使用说明请参考项目中的 `用户指南-Markdown和内容管理.md` 文档。

### Markdown 格式支持

文章内容支持Markdown格式，您可以使用以下语法：

1. **标题**: 使用 `#` 符号，例如 `# 一级标题`、`## 二级标题`
2. **列表**:
   - 无序列表：使用 `-` 或 `*` 
   - 有序列表：使用 `1.` `2.` 等
3. **强调**:
   - 斜体：使用 `*文字*` 或 `_文字_`
   - 粗体：使用 `**文字**` 或 `__文字__`
4. **代码**:
   - 行内代码：使用反引号 \`code\`
   - 代码块：使用三个反引号
5. **链接**: `[链接文本](URL)`
6. **图片**: `![替代文本](图片URL)`
7. **表格**: 支持Markdown表格语法
8. **引用**: 使用 `>` 符号

### 内容管理

- **创建内容**: 登录后可以发布文章、图片和视频等内容
- **编辑内容**: 内容创建者可以编辑自己的内容
- **删除内容**: 内容创建者和管理员可以删除内容
  - 非遗项目: 创建者可以删除自己的项目（若无关联内容）
  - 论坛主题: 创建者可以删除自己的主题和回复

## 故障排除指南

### 1. 数据库连接错误
   - 确保 MySQL 服务已启动
   - 检查 `config.py` 中的数据库连接信息是否正确
   - 确保数据库用户有足够的权限

### 2. 500 服务器错误
   - 查看控制台输出的错误日志
   - 检查 `logs` 目录中的错误记录
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


## 贡献指南

欢迎参与项目开发和改进，您可以通过以下方式贡献：

1. 报告问题和建议
2. 提交功能改进请求
3. 提交代码修复或新功能实现

在提交代码前，请确保您的代码符合项目的代码规范并通过基本测试。

## 许可证

本项目采用MIT许可证 - 详见[LICENSE](LICENSE)文件

Copyright (c) 2025 体育非遗数字展示平台
