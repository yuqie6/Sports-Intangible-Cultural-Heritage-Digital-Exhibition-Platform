# 中国社交媒体情绪地图 - 用户指南

## 简介

中国社交媒体情绪地图是一个数据工程开源项目，通过合法收集中国社交平台的公开数据，分析用户对特定话题的情绪倾向，并将结果以动态地图形式展示，反映全国各地对该话题的态度差异。

本指南将帮助您了解如何安装、配置和使用本工具。

## 安装与配置

### 系统要求

- Python 3.9 或更高版本
- 至少 4GB 内存
- 操作系统：Windows, macOS 或 Linux

### 安装步骤

1. 克隆项目仓库：
   ```bash
   git clone https://github.com/yourusername/china-social-media-sentiment-map.git
   cd china-social-media-sentiment-map
   ```

2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

3. 配置 API 密钥：
   - 复制 `config/api_keys_example.json` 为 `config/api_keys.json`
   - 编辑 `api_keys.json` 文件，添加相应平台的 API 密钥

## 使用方法

### 网页界面

启动 Streamlit 网页界面：

```bash
streamlit run app.py
```

在浏览器中访问提示的 URL（通常是 http://localhost:8501），您将看到情绪地图的 Web 界面。

#### 使用步骤：

1. 在左侧边栏输入**关键词**（例如："编程竞赛"）
2. 选择要分析的**平台**（知乎、微博）
3. 设置每个平台的**数据量**
4. 选择**情感分析领域**（通用、编程、教育等）
5. 点击**开始分析**按钮
6. 等待系统处理完成后，查看生成的情绪地图和数据分析

### 命令行工具

除了网页界面，您也可以通过命令行使用本工具：

```bash
python main.py --keyword "编程竞赛" --platforms zhihu,weibo --limit 100 --domain programming
```

参数说明：
- `--keyword`, `-k`: 搜索关键词（必需）
- `--platforms`, `-p`: 数据来源平台，逗号分隔（默认：zhihu,weibo）
- `--limit`, `-l`: 每个平台的数据条数限制（默认：使用配置文件中的设置）
- `--domain`, `-d`: 情感分析领域（默认：general）
- `--output`, `-o`: 输出目录（默认：output）
- `--config`, `-c`: 配置文件路径（默认：config/config.json）

### REST API

本工具还提供了 REST API，可以集成到其他应用程序中：

启动 API 服务器：
```bash
python api.py
```

API 服务默认在 5000 端口运行，主要端点：
- `/api/collect`: 采集数据
- `/api/analyze`: 分析数据
- `/api/visualize`: 生成可视化
- `/api/sentiment_map`: 完整处理流程

详细 API 文档请查看 `docs/api_doc.md`。

## 功能说明

### 情绪地图

情绪地图是本工具的核心功能，它将分析结果映射到中国地图上，使用颜色表示不同地区的情绪倾向：
- 红色：消极情绪
- 黄色：中性情绪
- 绿色：积极情绪

灰色区域表示数据不足，无法进行有效分析。

### 情感分布分析

情感分布图展示了所有收集数据的情感类别分布，包括：
- 非常积极
- 积极
- 中性
- 消极
- 非常消极
- 数据不足

### 平台对比

如果您选择了多个平台，系统将展示不同平台间的情绪差异，包括：
- 平台情绪得分对比
- 平台数据统计
- 平台间情绪地图对比

### 原始数据

系统提供原始处理数据的查看和下载功能，便于进一步分析或研究。

## 常见问题解答

**Q: 为什么某些地区显示为灰色？**
A: 灰色区域表示该地区的数据样本不足（默认少于5条），无法进行有效的情感分析。

**Q: 分析结果的准确性如何？**
A: 本工具结合了多种情感分析模型，包括SnowNLP、规则基础分析和领域词典分析。准确性取决于数据质量和分析模型，作为研究和参考工具使用时效果较好，但不宜用于商业决策。

**Q: 数据来源是否合规？**
A: 本工具仅获取公开的社交媒体内容，遵循各平台的API使用条款，并不会爬取非公开或需要授权的数据。

**Q: 如何添加新的情感分析领域？**
A: 在 `data/sentiment_dict/` 目录中添加新的JSON文件，格式参考已有的领域词典文件。

## 故障排除

**问题：安装依赖时出错**
- 尝试使用虚拟环境：`python -m venv venv` 然后激活环境
- 检查 Python 版本是否为 3.9 或更高

**问题：API认证失败**
- 检查 `api_keys.json` 文件配置是否正确
- 确认API密钥是否有效

**问题：无法识别地区信息**
- 地区识别依赖于社交媒体内容或用户资料中的地理信息
- 可以考虑扩充 `data/location_dict.json` 中的地区词典

## 联系与支持

如果您在使用过程中遇到问题，或有改进建议，请通过以下方式联系我们：

- GitHub Issues: https://github.com/yourusername/china-social-media-sentiment-map/issues
- 电子邮件: youremail@example.com
