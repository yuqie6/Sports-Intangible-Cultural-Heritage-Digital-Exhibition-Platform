"""模拟数据生成器，在真实数据采集不可用时提供样本数据"""

import random
import json
import os
import time
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MockDataGenerator:
    """模拟数据生成器"""
    
    def __init__(self, seed: int = None):
        """初始化模拟数据生成器
        
        Args:
            seed: 随机种子，用于生成可重复的数据
        """
        if seed is not None:
            random.seed(seed)
        
        # 加载模拟数据模板
        self.templates = self._load_templates()
        
        logger.info("模拟数据生成器初始化完成")
    
    def _load_templates(self) -> Dict[str, Any]:
        """加载模拟数据模板"""
        # 定义基本模板
        templates = {
            "zhihu": {
                "question_titles": [
                    "有哪些值得推荐的{keyword}平台？",
                    "{keyword}入门应该学习哪些内容？",
                    "如何评价最近的{keyword}活动？",
                    "大家平时都用什么{keyword}工具？",
                    "初学者如何参加{keyword}？",
                    "关于{keyword}，你有什么经验可以分享？",
                    "{keyword}的未来发展趋势是什么？",
                    "学生如何通过{keyword}提升自己？",
                    "参加{keyword}有什么好处？",
                    "国内外{keyword}水平差距在哪里？"
                ],
                "answers": [
                    "我认为{keyword}非常有价值，参加过很多次，收获很大。最重要的是坚持不懈地练习，不断挑战自己。",
                    "作为一个{keyword}爱好者，我想分享一些经验。首先，基础很重要；其次，多参与实践；最后，向优秀的人学习。",
                    "说实话，国内的{keyword}水平还有提升空间。相比国外，我们在创新性和系统性上有差距，但勤奋程度确实令人钦佩。",
                    "最近参加了一场{keyword}，感觉组织得很好，题目难度适中，平台也很稳定，推荐给大家。不过在细节上还有提升空间。",
                    "我觉得{keyword}最大的问题是门槛偏高，对新手不够友好。希望能有更多入门级的资源和活动。"
                ],
                "authors": [
                    "编程爱好者", "技术达人", "学习者007", "热心网友", "行业专家",
                    "计算机学生", "软件工程师", "数据科学家", "产品经理", "教育工作者"
                ],
                "locations": [
                    "北京", "上海", "广州", "深圳", "杭州", 
                    "成都", "武汉", "西安", "南京", "苏州", 
                    "长沙", "重庆", "天津", "青岛", "宁波"
                ]
            },
            "weibo": {
                "posts": [
                    "今天参加了{keyword}活动，感觉很充实！#每日学习打卡#",
                    "分享一个{keyword}的小技巧：{tip}，希望对大家有帮助！",
                    "求助：有没有推荐的{keyword}平台或工具？新手想入门",
                    "{keyword}真的太难了，学习曲线陡峭啊，有没有同感的朋友？ ",
                    "最近在研究{keyword}相关的项目，有没有同学想一起探讨？",
                    "推荐一本关于{keyword}的好书：《{book}》，读完收获很大！",
                    "参加{keyword}比赛得了奖，心情超级好！感谢团队的每个人！",
                    "为什么国内的{keyword}资源这么少？特别是高质量的中文教程",
                    "{keyword}到底有没有必要学？纠结ing...",
                    "分享我的{keyword}学习心得：坚持 > 天赋，持续积累很重要"
                ],
                "tips": [
                    "多做练习", "看官方文档", "参加社区活动", "跟着项目学习", 
                    "做好笔记", "定期复习", "教会别人", "写博客"
                ],
                "books": [
                    "从入门到精通", "实战指南", "权威教程", "最佳实践", 
                    "核心原理", "编程之美", "深入浅出", "编程珠玑"
                ],
                "authors": [
                    "程序员日常", "IT爱好者", "编程学习笔记", "码农的自我修养", 
                    "科技最前沿", "互联网分析", "学习打卡", "代码人生"
                ],
                "locations": [
                    "北京", "上海", "广州", "深圳", "杭州", 
                    "成都", "武汉", "西安", "南京", "苏州"
                ]
            },
            "xiaohongshu": {
                "titles": [
                    "分享一下我的{keyword}心得",
                    "超实用{keyword}技巧",
                    "{keyword}学习日记",
                    "关于{keyword}，你不得不知道的事情",
                    "我的{keyword}挑战30天",
                    "{keyword}入门攻略",
                    "零基础如何学习{keyword}",
                    "{keyword}学习资源推荐",
                    "我是如何自学{keyword}的",
                    "小白必看：{keyword}避坑指南"
                ],
                "contents": [
                    "今天给大家分享一下我学习{keyword}的经验。首先，建立正确的学习方法很重要；其次，要坚持每天练习；最后，多和圈内的朋友交流。#学习打卡 #经验分享",
                    "{keyword}真的很有趣！我已经坚持学习一个月了，感觉自己进步很大。分享几个实用技巧：1.系统学习比碎片化学习效果好 2.多做项目练习 3.遇到问题多查资料，独立思考。",
                    "刚开始学{keyword}时走了不少弯路，现在把我的学习路径分享给大家：先打好基础，然后针对性练习，最后做实战项目。希望对你们有帮助！#新手指南",
                    "推荐几个学习{keyword}的好资源：1.官方文档永远是最好的教程 2.B站上XXX的视频讲解很清晰 3.《XXX入门与实践》这本书 4.GitHub上的XXX项目。都是我反复学习的好东西！",
                    "学习{keyword}一个月，最大感受：坚持很重要！哪怕每天只学15分钟，一个月下来也会有很大进步。今天分享我的学习笔记和心得体会，希望对同路人有所帮助。"
                ],
                "authors": [
                    "学习笔记", "知识分享官", "编程爱好者", "自学达人", 
                    "热爱生活的程序媛", "技术博主", "代码搬运工", "程序员日常",
                    "IT修炼生", "互联网小白"
                ],
                "locations": [
                    "北京", "上海", "广州", "深圳", "杭州", 
                    "成都", "武汉", "西安", "南京", "苏州"
                ]
            }
        }
        
        # 尝试加载自定义模板（如果存在）
        custom_template_path = "data/mock_templates.json"
        if os.path.exists(custom_template_path):
            try:
                with open(custom_template_path, 'r', encoding='utf-8') as f:
                    custom_templates = json.load(f)
                # 合并自定义模板
                for platform, data in custom_templates.items():
                    if platform in templates:
                        for key, values in data.items():
                            if key in templates[platform]:
                                templates[platform][key].extend(values)
                            else:
                                templates[platform][key] = values
                    else:
                        templates[platform] = data
                logger.info(f"已加载自定义模板: {custom_template_path}")
            except Exception as e:
                logger.warning(f"无法加载自定义模板: {str(e)}")
        
        return templates
    
    def generate_data(self, keyword: str, platform: str, count: int) -> List[Dict]:
        """生成模拟数据
        
        Args:
            keyword: 关键词，用于填充模板
            platform: 平台名称，如"zhihu"或"weibo"
            count: 生成的数据条数
            
        Returns:
            List[Dict]: 生成的模拟数据
        """
        if platform not in self.templates:
            logger.warning(f"不支持的平台: {platform}")
            return []
        
        results = []
        template = self.templates[platform]
        
        # 根据平台生成不同的模拟数据
        if platform == "zhihu":
            for i in range(count):
                # 随机选择问题标题和回答
                title = random.choice(template["question_titles"]).replace("{keyword}", keyword)
                answer = random.choice(template["answers"]).replace("{keyword}", keyword)
                content = f"{title}: {answer}"
                
                # 随机生成其他信息
                author = random.choice(template["authors"])
                location = random.choice(template["locations"])
                publish_time = (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
                
                # 创建模拟数据项
                item = {
                    "platform": "zhihu",
                    "content_id": f"mock_zhihu_{int(time.time())}_{i}",
                    "content": content,
                    "author": author,
                    "location": location,
                    "publish_time": publish_time,
                    "extra_data": {
                        "type": random.choice(["answer", "article"]),
                        "url": f"https://www.zhihu.com/question/{random.randint(10000000, 99999999)}"
                    }
                }
                
                results.append(item)
                
        elif platform == "weibo":
            for i in range(count):
                # 随机组装微博内容
                post_template = random.choice(template["posts"])
                post = post_template.replace("{keyword}", keyword)
                
                # 填充可能的占位符
                if "{tip}" in post:
                    post = post.replace("{tip}", random.choice(template["tips"]))
                if "{book}" in post:
                    book = f"{keyword}{random.choice(template['books'])}"
                    post = post.replace("{book}", book)
                
                # 随机生成其他信息
                author = random.choice(template["authors"])
                location = random.choice(template["locations"])
                publish_time = (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
                
                # 创建模拟数据项
                item = {
                    "platform": "weibo",
                    "content_id": f"mock_weibo_{int(time.time())}_{i}",
                    "content": post,
                    "author": author,
                    "location": location,
                    "publish_time": publish_time,
                    "extra_data": {
                        "reposts_count": random.randint(0, 100),
                        "comments_count": random.randint(0, 50),
                        "attitudes_count": random.randint(0, 200)
                    }
                }
                
                results.append(item)
                
        elif platform == "xiaohongshu":
            for i in range(count):
                # 随机选择标题和内容
                title = random.choice(template["titles"]).replace("{keyword}", keyword)
                content = random.choice(template["contents"]).replace("{keyword}", keyword)
                full_content = f"{title}\n\n{content}"
                
                # 随机生成其他信息
                author = random.choice(template["authors"])
                location = random.choice(template["locations"])
                publish_time = (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
                
                # 创建模拟数据项
                item = {
                    "platform": "xiaohongshu",
                    "content_id": f"mock_xhs_{int(time.time())}_{i}",
                    "content": full_content,
                    "author": author,
                    "location": location,
                    "publish_time": publish_time,
                    "extra_data": {
                        "type": "note",
                        "url": f"https://www.xiaohongshu.com/discovery/item/{hex(random.randint(1000000, 9999999))[2:]}"
                    }
                }
                
                results.append(item)
                
        logger.info(f"已生成 {len(results)} 条 {platform} 模拟数据")
        return results
