import jieba
import os
import json
import numpy as np
from snownlp import SnowNLP
from typing import Dict, List, Tuple, Union, Optional
import logging

# 配置日志
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """多模型情感分析器"""
    
    def __init__(self, config: Dict = None, custom_dict_path: Optional[str] = None, 
                 domain: str = "general"):
        """初始化情感分析器
        
        Args:
            config: 配置字典
            custom_dict_path: 自定义词典路径
            domain: 领域，用于加载特定领域的情感词典
        """
        # 配置
        self.config = config or {}
        
        # 加载自定义词典
        self.custom_dict_path = custom_dict_path
        if custom_dict_path and os.path.exists(custom_dict_path):
            jieba.load_userdict(custom_dict_path)
            logger.info(f"已加载自定义词典: {custom_dict_path}")
        
        # 加载领域情感词典
        self.domain = domain
        self.sentiment_dict = self._load_sentiment_dict(domain)
        
        # 初始化模型权重
        weights_config = self.config.get("sentiment_analysis", {}).get("model_weights", {})
        self.model_weights = {
            "snownlp": weights_config.get("snownlp", 0.5),
            "rule_based": weights_config.get("rule_based", 0.3),
            "domain_dict": weights_config.get("domain_dict", 0.2)
        }
        
        # 情感阈值
        self.thresholds = self.config.get("sentiment_analysis", {}).get("thresholds", {
            "very_negative": 0.2,
            "negative": 0.4,
            "neutral": 0.6,
            "positive": 0.8,
            "very_positive": 1.0
        })
        
        logger.info(f"情感分析器初始化完成，使用领域: {domain}")
    
    def _load_sentiment_dict(self, domain: str) -> Dict[str, Dict[str, float]]:
        """加载领域情感词典
        
        Args:
            domain: 领域名称
        
        Returns:
            情感词典 {词: {"score": 得分, "weight": 权重}}
        """
        # 默认词典
        default_dict = {
            # 积极词汇
            "喜欢": {"score": 0.8, "weight": 1.0},
            "赞": {"score": 0.9, "weight": 1.0},
            "好": {"score": 0.7, "weight": 0.7},
            "棒": {"score": 0.8, "weight": 1.0},
            "优秀": {"score": 0.8, "weight": 1.0},
            "开心": {"score": 0.8, "weight": 1.0},
            "推荐": {"score": 0.7, "weight": 0.8},
            
            # 消极词汇
            "差": {"score": 0.2, "weight": 0.8},
            "烂": {"score": 0.1, "weight": 1.0},
            "失望": {"score": 0.2, "weight": 1.0},
            "问题": {"score": 0.3, "weight": 0.7},
            "bug": {"score": 0.2, "weight": 0.8},
            "难用": {"score": 0.2, "weight": 0.9},
            "坑": {"score": 0.2, "weight": 0.8}
        }
        
        # 领域特定词典路径
        domain_dict_path = f"data/sentiment_dict/{domain}.json"
        
        # 如果存在领域词典，则加载并合并
        if os.path.exists(domain_dict_path):
            try:
                with open(domain_dict_path, 'r', encoding='utf-8') as f:
                    domain_dict = json.load(f)
                # 合并词典，领域词典优先
                default_dict.update(domain_dict)
                logger.info(f"已加载领域词典: {domain_dict_path}")
            except Exception as e:
                logger.error(f"加载领域词典失败: {str(e)}")
        else:
            logger.warning(f"未找到领域词典: {domain_dict_path}，使用默认词典")
        
        return default_dict
    
    def analyze(self, text: str) -> Dict[str, Union[float, str]]:
        """综合多种方法分析文本情感
        
        Args:
            text: 输入文本
        
        Returns:
            Dict: {"score": 情感得分, "category": 情感类别, "confidence": 置信度}
        """
        if not text or len(text) < 5:  # 文本过短，不足以分析
            return {"score": 0.5, "category": "neutral", "confidence": 0.0}
        
        try:
            # SnowNLP分析
            try:
                snow_score = SnowNLP(text).sentiments
            except Exception as e:
                logger.warning(f"SnowNLP分析失败: {str(e)}")
                snow_score = 0.5  # 分析失败时默认为中性
            
            # 分词
            words = jieba.lcut(text)
            
            # 域词典分析
            domain_score = self._domain_dict_analyze(words)
            
            # 规则based分析
            rule_score = self._rule_based_analyze(text, words)
            
            # 加权平均
            final_score = (
                self.model_weights["snownlp"] * snow_score + 
                self.model_weights["rule_based"] * rule_score +
                self.model_weights["domain_dict"] * domain_score
            )
            
            # 确保分数在[0,1]范围内
            final_score = max(0.0, min(1.0, final_score))
            
            # 计算置信度: 模型间一致性
            scores = [snow_score, rule_score, domain_score]
            confidence = 1.0 - np.std(scores)  # 标准差越小，一致性越高
            
            return {
                "score": final_score,
                "category": self._score_to_category(final_score),
                "confidence": confidence,
                "model_scores": {
                    "snownlp": snow_score,
                    "rule_based": rule_score,
                    "domain_dict": domain_score
                }
            }
        except Exception as e:
            logger.error(f"情感分析失败: {str(e)}")
            return {"score": 0.5, "category": "neutral", "confidence": 0.0}
    
    def _domain_dict_analyze(self, words: List[str]) -> float:
        """基于领域词典的情感分析"""
        total_score = 0.0
        total_weight = 0.0
        
        for word in words:
            if word in self.sentiment_dict:
                entry = self.sentiment_dict[word]
                total_score += entry["score"] * entry["weight"]
                total_weight += entry["weight"]
        
        if total_weight == 0:
            return 0.5  # 中性
        
        return total_score / total_weight
    
    def _rule_based_analyze(self, text: str, words: List[str]) -> float:
        """基于规则的情感分析"""
        # 简单的情感词计数
        pos_words = ["喜欢", "赞", "好", "棒", "优秀", "开心", "推荐", "支持", "厉害", "强"]
        neg_words = ["差", "烂", "失望", "问题", "bug", "难用", "坑", "垃圾", "差劲", "弱"]
        
        pos_count = sum([1 for word in words if word in pos_words])
        neg_count = sum([1 for word in words if word in neg_words])
        
        # 否定词处理
        negation_words = ["不", "没", "无", "非", "莫", "弗", "勿", "毋", "未", "否"]
        for i, word in enumerate(words[:-1]):
            if word in negation_words:
                # 情感反转
                if i+1 < len(words):
                    if words[i+1] in pos_words:
                        pos_count -= 1
                        neg_count += 1
                    elif words[i+1] in neg_words:
                        neg_count -= 1
                        pos_count += 1
        
        # 情感强度词处理
        intensifiers = ["很", "非常", "特别", "极", "太", "真", "超"]
        for i, word in enumerate(words[:-1]):
            if word in intensifiers:
                # 增强情感强度
                if i+1 < len(words):
                    if words[i+1] in pos_words:
                        pos_count += 0.5
                    elif words[i+1] in neg_words:
                        neg_count += 0.5
        
        total = pos_count + neg_count
        if total == 0:
            return 0.5  # 中性
        
        return pos_count / total
    
    def _score_to_category(self, score: float) -> str:
        """将情感得分转换为类别"""
        if score < self.thresholds.get("very_negative", 0.2):
            return "very_negative"
        elif score < self.thresholds.get("negative", 0.4):
            return "negative"
        elif score < self.thresholds.get("neutral", 0.6):
            return "neutral"
        elif score < self.thresholds.get("positive", 0.8):
            return "positive"
        else:
            return "very_positive"
    
    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """批量分析多条文本"""
        results = []
        for text in texts:
            results.append(self.analyze(text))
        return results
    
    def create_domain_dict(self, domain: str, new_entries: Dict[str, Dict[str, float]]):
        """创建或更新领域情感词典
        
        Args:
            domain: 领域名称
            new_entries: 新词条 {词: {"score": 得分, "weight": 权重}}
        """
        # 确保目录存在
        os.makedirs("data/sentiment_dict", exist_ok=True)
        
        # 领域词典路径
        domain_dict_path = f"data/sentiment_dict/{domain}.json"
        
        # 加载现有词典（如果存在）
        existing_dict = {}
        if os.path.exists(domain_dict_path):
            with open(domain_dict_path, 'r', encoding='utf-8') as f:
                existing_dict = json.load(f)
        
        # 更新词典
        existing_dict.update(new_entries)
        
        # 保存更新后的词典
        with open(domain_dict_path, 'w', encoding='utf-8') as f:
            json.dump(existing_dict, f, ensure_ascii=False, indent=2)
        
        logger.info(f"领域词典 '{domain}' 已更新")
        
        # 重新加载当前实例的词典（如果更新的是当前使用的领域）
        if domain == self.domain:
            self.sentiment_dict = self._load_sentiment_dict(domain)

# 测试代码
if __name__ == "__main__":
    # 创建编程领域词典
    programming_dict = {
        "代码": {"score": 0.5, "weight": 0.5},
        "算法": {"score": 0.6, "weight": 0.6},
        "bug": {"score": 0.2, "weight": 0.8},
        "开源": {"score": 0.7, "weight": 0.7},
        "崩溃": {"score": 0.1, "weight": 0.9},
        "优化": {"score": 0.7, "weight": 0.7}
    }
    
    analyzer = SentimentAnalyzer(domain="programming")
    analyzer.create_domain_dict("programming", programming_dict)
    
    text = "这个编程竞赛平台设计得很好，题目难度适中，界面也很友好！推荐给所有编程爱好者。"
    result = analyzer.analyze(text)
    print(f"情感分析结果: {result}")
