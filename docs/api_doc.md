# 中国社交媒体情绪地图 - API 文档

本文档介绍中国社交媒体情绪地图提供的 REST API，可用于将情绪分析功能集成到其他应用中。

## API 基本信息

- **基础URL**: `http://localhost:5000`
- **响应格式**: JSON
- **认证方式**: 无（本地开发版本）

## API 端点

### 1. 首页信息

获取API基本信息。

**请求**:
```
GET /
```

**响应**:
```json
{
  "name": "中国社交媒体情绪地图 API",
  "version": "1.0.0",
  "endpoints": {
    "/api/collect": "采集数据 (POST)",
    "/api/analyze": "分析数据 (POST)",
    "/api/visualize": "生成可视化 (POST)",
    "/api/sentiment_map": "完整处理流程 (POST)"
  }
}
```

### 2. 采集数据

从社交媒体平台采集关键词相关数据。

**请求**:
```
POST /api/collect
```

**请求参数**:
```json
{
  "keyword": "编程竞赛",
  "platforms": ["zhihu", "weibo"],
  "limit": 100,
  "use_cache": true
}
```

参数说明:
- `keyword` (必需): 搜索关键词
- `platforms` (可选): 平台列表，默认为 ["zhihu"]
- `limit` (可选): 每个平台的数据条数限制
- `use_cache` (可选): 是否使用缓存数据，默认为 true

**响应**:
```json
{
  "success": true,
  "keyword": "编程竞赛",
  "total_count": 150,
  "platform_counts": {
    "zhihu": 100,
    "weibo": 50
  },
  "elapsed_time": 3.45,
  "data_summary": {
    "zhihu": {
      "count": 100,
      "sample": {
        "platform": "zhihu",
        "content_id": "12345678",
        "content": "这个编程竞赛平台很好用...",
        "author": "用户名",
        "location": "北京",
        "publish_time": "2025-03-15T10:30:45"
      }
    },
    "weibo": {
      "count": 50,
      "sample": {
        "platform": "weibo",
        "content_id": "87654321",
        "content": "参加了一场很有意思的编程竞赛...",
        "author": "微博用户",
        "location": "上海",
        "publish_time": "2025-03-14T18:20:33"
      }
    }
  }
}
```

### 3. 分析数据

分析已采集的数据或通过关键词重新采集并分析数据。

**请求**:
```
POST /api/analyze
```

**请求参数**:
```json
{
  "keyword": "编程竞赛",
  "platforms": ["zhihu", "weibo"],
  "domain": "programming"
}
```

或提供原始数据:
```json
{
  "raw_data": {
    "zhihu": [
      {
        "platform": "zhihu",
        "content_id": "12345678",
        "content": "这个编程竞赛平台很好用...",
        "author": "用户名",
        "location": "北京",
        "publish_time": "2025-03-15T10:30:45"
      }
    ]
  },
  "domain": "programming"
}
```

参数说明:
- `keyword` 或 `raw_data` (必需其一): 搜索关键词或原始数据
- `platforms` (可选，当使用keyword时): 平台列表
- `domain` (可选): 情感分析领域，默认为 "general"

**响应**:
```json
{
  "success": true,
  "data_count": 120,
  "province_count": 15,
  "elapsed_time": 2.34,
  "sentiment_distribution": {
    "very_positive": 30,
    "positive": 45,
    "neutral": 25,
    "negative": 15,
    "very_negative": 5
  },
  "province_data": {
    "北京": {
      "score": 0.75,
      "count": 20,
      "categories": {
        "positive": 12,
        "very_positive": 5,
        "neutral": 3
      }
    },
    "上海": {
      "score": 0.68,
      "count": 15,
      "categories": {
        "positive": 8,
        "neutral": 5,
        "negative": 2
      }
    }
  }
}
```

### 4. 生成可视化

根据提供的省份数据生成情绪地图。

**请求**:
```
POST /api/visualize
```

**请求参数**:
```json
{
  "province_data": {
    "北京": {
      "score": 0.75,
      "count": 20
    },
    "上海": {
      "score": 0.68,
      "count": 15
    }
  },
  "title": "编程竞赛情绪地图"
}
```

参数说明:
- `province_data` (必需): 省份情绪数据
- `title` (可选): 地图标题

**响应**:
HTML文件（情绪地图），以附件形式返回。

### 5. 完整处理流程

一次性执行完整的数据处理流程，从数据采集到可视化生成。

**请求**:
```
POST /api/sentiment_map
```

**请求参数**:
```json
{
  "keyword": "编程竞赛",
  "platforms": ["zhihu", "weibo"],
  "limit": 100,
  "domain": "programming"
}
```

参数说明:
- `keyword` (必需): 搜索关键词
- `platforms` (可选): 平台列表，默认为 ["zhihu"]
- `limit` (可选): 每个平台的数据条数限制
- `domain` (可选): 情感分析领域，默认为 "general"

**响应**:
```json
{
  "success": true,
  "task_id": "编程竞赛_20250321123456",
  "keyword": "编程竞赛",
  "status": "completed",
  "data_count": 150,
  "province_count": 18,
  "elapsed_time": 8.76,
  "files": {
    "map": "/tmp/编程竞赛_20250321123456/sentiment_map.html",
    "data": "/tmp/编程竞赛_20250321123456/processed_data.csv",
    "distribution": "/tmp/编程竞赛_20250321123456/sentiment_distribution.html",
    "platform_comparison": "/tmp/编程竞赛_20250321123456/platform_comparison.html"
  },
  "result_dir": "/tmp/编程竞赛_20250321123456"
}
```

### 6. 获取任务状态

检查任务处理状态。

**请求**:
```
GET /api/task/<task_id>
```

**响应**:
```json
{
  "success": true,
  "task": {
    "status": "completed",
    "keyword": "编程竞赛",
    "start_time": "2025-03-21T12:34:56",
    "progress": 100,
    "elapsed_time": 8.76,
    "result_dir": "/tmp/编程竞赛_20250321123456"
  }
}
```

可能的任务状态:
- `started`: 任务已开始
- `collecting`: 正在采集数据
- `processing`: 正在处理数据
- `aggregating`: 正在聚合数据
- `visualizing`: 正在生成可视化
- `completed`: 任务已完成
- `failed`: 任务失败

## 错误处理

当API请求出错时，将返回包含错误信息的JSON响应:

```json
{
  "success": false,
  "error": "错误信息描述"
}
```

常见错误码:
- 400: 请求参数错误
- 404: 资源不存在
- 500: 服务器内部错误

## 使用示例

### Python示例：分析关键词情绪

```python
import requests
import json

# API基础URL
base_url = "http://localhost:5000"

# 分析关键词情绪
def analyze_keyword_sentiment(keyword, platforms=["zhihu"], domain="general"):
    # 构建请求
    url = f"{base_url}/api/sentiment_map"
    payload = {
        "keyword": keyword,
        "platforms": platforms,
        "domain": domain
    }
    
    # 发送请求
    response = requests.post(url, json=payload)
    
    # 检查响应
    if response.status_code == 200:
        result = response.json()
        if result["success"]:
            print(f"分析完成! 任务ID: {result['task_id']}")
            print(f"数据量: {result['data_count']} 条")
            print(f"情绪地图文件: {result['files']['map']}")
            return result
        else:
            print(f"分析失败: {result['error']}")
    else:
        print(f"API请求失败: HTTP {response.status_code}")
    
    return None

# 使用示例
if __name__ == "__main__":
    result = analyze_keyword_sentiment("编程竞赛", ["zhihu"], "programming")
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

### JavaScript示例：获取任务状态

```javascript
async function getTaskStatus(taskId) {
    try {
        const response = await fetch(`http://localhost:5000/api/task/${taskId}`);
        const data = await response.json();
        
        if (data.success) {
            console.log(`任务状态: ${data.task.status}`);
            console.log(`进度: ${data.task.progress}%`);
            return data.task;
        } else {
            console.error(`获取任务状态失败: ${data.error}`);
            return null;
        }
    } catch (error) {
        console.error(`API请求错误: ${error.message}`);
        return null;
    }
}

// 使用示例
getTaskStatus("编程竞赛_20250321123456")
    .then(task => {
        if (task && task.status === "completed") {
            console.log("任务已完成！");
            console.log(`结果目录: ${task.result_dir}`);
        }
    });
```

## 注意事项

1. 所有请求均使用UTF-8编码
2. 大数据量处理可能需要较长时间
3. 建议客户端实现任务状态轮询机制
4. 临时文件会定期清理，请及时下载或保存结果
