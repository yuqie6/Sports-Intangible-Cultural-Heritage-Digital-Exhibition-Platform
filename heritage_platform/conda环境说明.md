# Conda环境设置指南

本项目使用Conda虚拟环境进行开发。以下是环境设置和使用的相关说明。

## 前提条件

- 已安装Anaconda或Miniconda
- 将Conda添加到系统环境变量中

## 环境设置步骤

1. 创建并激活环境：

```bash
# 创建名为heritage_env的Python 3.9环境
conda create -n heritage_env python=3.9
# 激活环境
conda activate heritage_env
```

2. 安装依赖包：

```bash
# 使用conda安装主要依赖
conda install -c conda-forge flask flask-login flask-sqlalchemy flask-wtf flask-migrate pymysql pillow
# 使用pip安装其他依赖
pip install email_validator
```

3. 保存依赖列表：

```bash
pip freeze > requirements.txt
```

## 日常使用

- **激活环境**：`conda activate heritage_env`
- **退出环境**：`conda deactivate`
- **查看已安装包**：`conda list`
- **更新环境**：`conda update --all`

## 项目脚本

项目提供了几个批处理脚本来简化环境管理和应用启动：

- `管理conda环境.bat`：提供环境创建、激活、退出等功能的菜单
- `安装依赖.bat`：创建环境并安装所有必要依赖
- `初始化数据库.bat`：激活环境并初始化数据库
- `启动应用.bat`：激活环境并启动Flask应用

## 注意事项

- 确保在操作项目代码之前已激活Conda环境
- 安装新的依赖后，记得更新`requirements.txt`
- 如遇到环境问题，可尝试重新创建环境
