# 故障排除指南

## 地图无法显示问题

如果在Web界面或导出的HTML中无法看到地图，请尝试以下解决方案：

### 1. 生成静态地图图片

我们提供了一个专门的工具来生成静态地图图片，可以解决在某些环境下无法正常显示HTML地图的问题：

```bash
python generate_static_maps.py --title "你的地图标题" --output "输出目录"
```

这将生成HTML和PNG格式的地图文件。

### 2. 确保安装了正确的依赖

确保安装了所有必要的依赖，特别是用于生成静态图片的依赖：

```bash
pip install pyecharts snapshot-selenium
```

### 3. 如果使用的是Windows系统

Windows系统可能需要额外安装Microsoft Visual C++ Redistributable，可以从Microsoft官网下载并安装。

### 4. 尝试不同的浏览器

有时候地图在某些浏览器中可能无法正常显示，请尝试使用Chrome或Firefox最新版本打开生成的HTML文件。

## 数据采集问题

### 知乎数据采集失败

知乎有较强的反爬虫机制，如果遇到问题，可以：

1. 更新你的cookies（需要登录知乎账号获取）
2. 在配置中将`use_mock_data`设置为`true`，使用模拟数据
3. 切换到其他平台如小红书或微博

### 小红书数据采集

小红书的数据采集需要设置正确的cookies才能正常工作。请确保：

1. 已经在`config/api_keys.json`中设置了有效的小红书cookies
2. 如果看到"登录墙"警告，说明cookies无效或已过期，需要更新

### 微博API限制

微博API有调用频率限制，如果遇到限制，可以：

1. 等待一段时间后再试
2. 在系统调试模式下使用模拟数据

## 其他常见问题

### 地区信息不足

如果地图上很多省份显示为灰色（数据不足），可能是因为：

1. 社交媒体上的内容缺少地区信息
2. 样本数量不够
3. 地区识别算法未能正确提取位置

解决方案：

1. 增加采集的数据量（提高`limit`参数）
2. 在`config/config.json`中降低`minimum_samples`的值
3. 扩展`data/location_dict.json`中的地区词典
