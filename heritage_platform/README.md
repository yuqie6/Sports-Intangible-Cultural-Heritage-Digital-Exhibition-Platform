# 体育非遗数字展示平台

连接课堂学习与数字化分享，促进体育非遗文化的传播与保护。

## 项目启动步骤

1. **准备环境**
   - 确保已安装 Anaconda 或 Miniconda
   - 确保 MySQL 服务已启动
   - 修改 `config.py` 中的数据库连接信息以匹配您的环境

2. **设置 Conda 环境**
   - 运行 `g:\项目赛\管理conda环境.bat` 并选择选项1创建环境，或者
   - 直接运行 `g:\项目赛\安装依赖.bat` 创建环境并安装依赖

3. **初始化数据库**
   - 运行 `g:\项目赛\heritage_platform\初始化数据库.bat`
   - 这会创建必要的数据库表和初始用户

4. **启动应用**
   - 运行 `g:\项目赛\heritage_platform\启动应用.bat`
   - 应用将在 http://127.0.0.1:5000 启动

## 默认用户

- 管理员：username: `admin`, password: `adminpassword`
- 教师：username: `teacher`, password: `teacherpassword`
- 学生：username: `student`, password: `studentpassword`

## 项目结构

```
heritage_platform/
├── app/                     # 应用主目录
│   ├── models/              # 数据模型
│   ├── routes/              # 路由控制
│   ├── templates/           # HTML模板
│   ├── static/              # 静态文件
│   ├── forms/               # 表单类
│   └── utils/               # 工具函数
├── config.py                # 配置文件
├── run.py                   # 启动脚本
└── init_db.py               # 数据库初始化
```

## 故障排除

如果遇到问题：

1. 确保 MySQL 服务已启动
2. 确保 `config.py` 中的数据库连接信息正确
3. 确保已激活 Conda 环境
4. 检查控制台输出中的错误信息

## 开发说明

项目使用 Flask 框架开发，采用蓝图结构组织代码。开发新功能时，请遵循以下步骤：

1. 在 models/ 中定义数据模型
2. 在 forms/ 中创建相关表单
3. 在 routes/ 中实现路由逻辑
4. 在 templates/ 中创建页面模板
5. 测试并确保功能正常工作
