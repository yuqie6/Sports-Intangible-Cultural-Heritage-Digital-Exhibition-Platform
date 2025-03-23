# 中国社交媒体情绪地图 (China Social Media Sentiment Map)

![版本](https://img.shields.io/badge/版本-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![许可证](https://img.shields.io/badge/许可证-MIT-yellow)

## 项目概述

"中国社交媒体情绪地图"是一个创新的数据工程开源项目，通过合法收集中国社交平台的公开数据，分析用户对特定话题的情绪倾向，并将结果以动态地图形式展示，反映全国各地对该话题的态度差异。

![示例地图](static/images/example_map.png)

## 主要功能

- **关键词分析**：输入任意关键词，获取相关社交媒体内容的情绪分析
- **多平台数据**：支持知乎、微博等平台的数据采集和分析
- **情绪地图**：以中国地图的形式直观展示各地区的情绪倾向
- **情绪对比**：支持不同平台间的情绪对比
- **数据导出**：支持分析结果的导出和分享

## 快速开始

### 安装

1. 克隆项目仓库：
```bash
git clone https://github.com/yourusername/china-social-media-sentiment-map.git
cd china-social-media-sentiment-map
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置API密钥：
```bash
cp config/api_keys_example.json config/api_keys.json
# 编辑 api_keys.json 文件，添加您的API密钥
```

### 使用

运行Web应用：
```bash
streamlit run app.py
```

或者使用命令行：
```bash
python main.py --keyword "编程竞赛" --platforms zhihu,weibo
```

## 项目结构

详见 [project_structure.txt](project_structure.txt)

## 技术栈

- **数据采集**：Requests, Selenium
- **文本处理**：jieba, pkuseg
- **情感分析**：SnowNLP, HanLP
- **数据存储**：SQLite
- **可视化**：pyecharts, Matplotlib, Plotly
- **Web界面**：Streamlit, Flask

## 贡献指南

欢迎贡献代码、报告问题或提出建议！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与项目。

## 许可证

本项目采用 MIT 许可证 - 详情请查看 [LICENSE](LICENSE) 文件。

## 联系方式

- 项目维护者：[Your Name](mailto:youremail@example.com)
- 项目仓库：[GitHub](https://github.com/yourusername/china-social-media-sentiment-map)
