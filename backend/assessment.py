import json
import requests
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL
import numpy as np

class UserAssessmentAnalyzer:
    """用户兴趣评估分析器"""
    
    def analyze_answers(self, answers):
        """分析用户答案并生成评估结果"""
        print("分析用户兴趣评估答案...")
        
        # 1. 基础分析 - 将答案转换为量化特征
        feature_scores = self._convert_answers_to_features(answers)
        
        # 2. 生成评估描述（使用DeepSeek API辅助）
        assessment_description = self._generate_assessment_description(answers, feature_scores)
        
        # 3. 综合结果
        assessment_result = {
            "feature_scores": feature_scores,
            "description": assessment_description,
            "preferred_types": self._determine_preferred_types(feature_scores),
            "travel_style": self._determine_travel_style(answers)
        }
        
        return assessment_result
    
    def _convert_answers_to_features(self, answers):
        """将用户答案转换为量化特征"""
        features = {
            "nature": 0,       # 自然景观偏好
            "culture": 0,      # 文化历史偏好
            "city": 0,         # 城市观光偏好
            "adventure": 0,    # 冒险体验偏好
            "relaxation": 0,   # 休闲放松偏好
            "food": 0,         # 美食偏好
            "crowd_tolerance": 0,  # 对拥挤的容忍度
            "budget_sensitivity": 0  # 对价格的敏感度
        }
        
        # 分析问题1：旅游类型偏好
        q1 = answers.get("q1", "")
        if q1 == "自然风光":
            features["nature"] += 3
        elif q1 == "历史文化":
            features["culture"] += 3
        elif q1 == "都市观光":
            features["city"] += 3
        elif q1 == "主题乐园":
            features["adventure"] += 2
            features["relaxation"] += 1
        elif q1 == "美食探索":
            features["food"] += 3
        
        # 分析问题2：旅游注重方面
        q2 = answers.get("q2", "")
        if q2 == "放松休闲":
            features["relaxation"] += 3
        elif q2 == "刺激冒险":
            features["adventure"] += 3
        elif q2 == "文化体验":
            features["culture"] += 3
        elif q2 == "拍照打卡":
            features["nature"] += 2
            features["city"] += 2
        elif q2 == "美食享受":
            features["food"] += 3
        
        # 分析问题3：旅行节奏
        q3 = answers.get("q3", "")
        if q3 == "慢节奏深度游":
            features["relaxation"] += 2
            features["culture"] += 1
        elif q3 == "紧凑观光":
            features["city"] += 2
            features["nature"] += 1
        elif q3 == "灵活随意":
            features["adventure"] += 2
            features["relaxation"] += 1
        
        # 分析问题4：感兴趣的活动
        q4 = answers.get("q4", [])
        for activity in q4:
            if activity == "徒步":
                features["nature"] += 1
                features["adventure"] += 1
            elif activity == "购物":
                features["city"] += 1
            elif activity == "博物馆":
                features["culture"] += 1
            elif activity == "品尝当地美食":
                features["food"] += 1
            elif activity == "夜生活":
                features["city"] += 1
                features["adventure"] += 1
            elif activity == "参观历史古迹":
                features["culture"] += 1
            elif activity == "水上活动":
                features["nature"] += 1
                features["adventure"] += 1
        
        # 分析问题5：对拥挤程度的接受度
        q5 = answers.get("q5", "")
        if q5 == "非常安静":
            features["crowd_tolerance"] = 1
        elif q5 == "适中":
            features["crowd_tolerance"] = 2
        elif q5 == "热闹":
            features["crowd_tolerance"] = 3
        
        # 分析问题6：对消费水平的敏感度
        q6 = answers.get("q6", "")
        if q6 == "非常敏感":
            features["budget_sensitivity"] = 3
        elif q6 == "一般":
            features["budget_sensitivity"] = 2
        elif q6 == "不敏感":
            features["budget_sensitivity"] = 1
        
        # 归一化特征值（0-10范围）
        max_possible = {
            "nature": 7, "culture": 7, "city": 7, "adventure": 7, 
            "relaxation": 6, "food": 6, "crowd_tolerance": 3, "budget_sensitivity": 3
        }
        
        for key in features:
            # 归一化到0-10范围
            features[key] = round((features[key] / max_possible[key]) * 10, 1)
        
        return features
    
    def _determine_preferred_types(self, feature_scores):
        """确定用户偏好的景点类型"""
        sorted_features = sorted(feature_scores.items(), key=lambda x: x[1], reverse=True)
        # 取前3个偏好
        return [feature[0] for feature in sorted_features[:3] if feature[0] not in ["crowd_tolerance", "budget_sensitivity"]]
    
    def _determine_travel_style(self, answers):
        """确定用户的旅行风格"""
        # 简单的规则判断
        if answers.get("q3") == "慢节奏深度游" and answers.get("q5") in ["非常安静", "适中"]:
            return "深度体验型"
        elif answers.get("q3") == "紧凑观光" and len(answers.get("q4", [])) >= 3:
            return "全面探索型"
        elif answers.get("q2") == "刺激冒险" or "水上活动" in answers.get("q4", []):
            return "冒险探索型"
        elif answers.get("q2") == "放松休闲" or answers.get("q3") == "灵活随意":
            return "休闲度假型"
        elif answers.get("q2") == "美食享受" or "品尝当地美食" in answers.get("q4", []):
            return "美食探索型"
        else:
            return "综合均衡型"
    
    def _generate_assessment_description(self, answers, feature_scores):
        """生成评估描述（使用DeepSeek API辅助）"""
        # 构建提示词
        prompt = f"""
        请分析以下用户的旅游偏好回答，并基于提供的特征评分，生成一段简洁的用户旅游偏好描述（100-150字）。
        
        用户回答：
        1. 喜欢的旅游类型：{answers.get('q1', '')}
        2. 旅游时注重：{answers.get('q2', '')}
        3. 旅行节奏偏好：{answers.get('q3', '')}
        4. 感兴趣的活动：{', '.join(answers.get('q4', []))}
        5. 对拥挤程度的接受度：{answers.get('q5', '')}
        6. 对消费水平的敏感度：{answers.get('q6', '')}
        7. 喜欢的旅行季节：{', '.join(answers.get('q7', []))}
        
        特征评分：
        {json.dumps(feature_scores, ensure_ascii=False, indent=2)}
        
        请生成一段自然流畅的描述，总结该用户的旅游偏好和特点。
        """
        
        # 如果没有API密钥，使用简单的描述生成
        if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == 'your_deepseek_api_key':
            return f"该用户偏好{answers.get('q1', '各类')}旅游，注重{answers.get('q2', '')}，喜欢{answers.get('q3', '')}的旅行节奏。对{', '.join(answers.get('q4', []))}等活动感兴趣。"
        
        # 调用DeepSeek API生成描述
        try:
            response = requests.post(
                DEEPSEEK_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"DeepSeek API调用失败: {response.text}")
                # 失败时返回默认描述
                return f"该用户偏好{answers.get('q1', '各类')}旅游，注重{answers.get('q2', '')}，喜欢{answers.get('q3', '')}的旅行节奏。"
        except Exception as e:
            print(f"调用DeepSeek API时发生错误: {e}")
            # 出错时返回默认描述
            return f"该用户偏好{answers.get('q1', '各类')}旅游，注重{answers.get('q2', '')}，喜欢{answers.get('q3', '')}的旅行节奏。"


class AttractionAssessor:
    """景点评估器"""
    
    def assess_attraction(self, attraction_data):
        """评估景点（这里主要是对爬取的数据进行进一步处理）"""
        # 在实际应用中，这里可以对爬取的景点数据进行更深入的分析
        # 例如：分析评论情感、提取关键词等
        
        # 1. 分析评论情感（简单示例）
        self._analyze_reviews_sentiment(attraction_data)
        
        # 2. 生成更详细的评估总结（使用DeepSeek API辅助）
        self._generate_detailed_assessment(attraction_data)
        
        return attraction_data
    
    def _analyze_reviews_sentiment(self, attraction_data):
        """简单的评论情感分析"""
        if "reviews" not in attraction_data:
            return
        
        for review in attraction_data["reviews"]:
            # 简单基于评分判断情感，实际应用中可以使用更复杂的NLP方法
            rating = float(review.get("rating", 3))
            if rating >= 4:
                review["sentiment"] = "positive"
            elif rating <= 2.5:
                review["sentiment"] = "negative"
            else:
                review["sentiment"] = "neutral"
    
    def _generate_detailed_assessment(self, attraction_data):
        """生成详细的景点评估（使用DeepSeek API辅助）"""
        # 构建提示词
        prompt = f"""
        请基于以下景点信息和游客评论，生成一段100-150字的景点评估总结，包括景点的主要特色、优势和可能的不足。
        
        景点信息：
        名称：{attraction_data.get('name', '')}
        类型：{attraction_data.get('type', '')}
        描述：{attraction_data.get('description', '')[:200]}
        评分：{attraction_data.get('overall_score', '')}
        
        部分游客评论：
        {json.dumps([r.get('content', '') for r in attraction_data.get('reviews', [])[:3]], ensure_ascii=False, indent=2)}
        
        请生成一段客观、全面的评估总结。
        """
        
        # 如果没有API密钥，使用现有总结
        if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == 'your_deepseek_api_key':
            return
        
        # 调用DeepSeek API生成评估
        try:
            response = requests.post(
                DEEPSEEK_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                attraction_data["assessment_summary"] = result["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"调用DeepSeek API生成景点评估时发生错误: {e}")
    
    def calculate_match_score(self, user_assessment, attraction_data):
        """计算用户与景点的匹配度"""
        if not user_assessment or not user_assessment.get("feature_scores"):
            return 0.5  # 默认匹配度50%
        
        user_features = user_assessment["feature_scores"]
        attraction_scores = attraction_data.get("assessment_scores", {})
        
        # 定义特征映射关系
        feature_mapping = {
            "nature": "scenery",       # 用户自然偏好 <-> 景点风景评分
            "culture": "culture",      # 用户文化偏好 <-> 景点文化评分
            "city": "facility",        # 用户城市偏好 <-> 景点设施评分
            "adventure": "facility",   # 用户冒险偏好 <-> 景点设施评分
            "relaxation": "service",   # 用户休闲偏好 <-> 景点服务评分
            "food": "value",           # 用户美食偏好 <-> 景点性价比评分
        }
        
        # 计算匹配度
        scores = []
        for user_feature, attraction_feature in feature_mapping.items():
            # 标准化到0-1范围
            user_score = user_features[user_feature] / 10
            attraction_score = attraction_scores.get(attraction_feature, 5) / 10  # 默认5分
            
            # 计算该维度的匹配度（1 - 两者差值的绝对值）
            match = 1 - abs(user_score - attraction_score)
            scores.append(match)
        
        # 考虑景点类型与用户偏好的匹配
        user_preferred_types = user_assessment.get("preferred_types", [])
        attraction_type = attraction_data.get("type", "")
        
        type_match = 0.5  # 默认类型匹配度
        if attraction_type:
            type_keywords = {
                "自然风光": ["nature"],
                "历史文化": ["culture"],
                "都市观光": ["city"],
                "主题乐园": ["adventure", "facility"],
                "美食探索": ["food"]
            }
            
            for type_name, keywords in type_keywords.items():
                if type_name in attraction_type:
                    # 检查用户是否偏好该类型
                    type_score = sum(1 for kw in keywords if kw in user_preferred_types) / len(keywords)
                    type_match = 0.5 + type_score * 0.5  # 0.5-1.0
                    break
        
        # 综合匹配度（加权平均）
        features_average = sum(scores) / len(scores)
        overall_match = (features_average * 0.7) + (type_match * 0.3)
        
        return round(overall_match, 2)
