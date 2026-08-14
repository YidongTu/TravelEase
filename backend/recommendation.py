import numpy as np
from database import db, City, Attraction, UserAssessment

class RecommendationEngine:
    """推荐引擎"""
    
    def get_recommendations(self, user_id, city_filter=None):
        """为用户生成景点推荐"""
        # 1. 获取用户评估数据
        user_assessment = UserAssessment.query.filter_by(user_id=user_id).first()
        if not user_assessment or not user_assessment.assessment_result:
            return {"message": "请先完成兴趣评估", "recommendations": []}
        
        # 2. 获取符合条件的景点（可选城市过滤）
        attractions = self._get_qualified_attractions(city_filter)
        if not attractions:
            return {"message": "未找到符合条件的景点", "recommendations": []}
        
        # 3. 计算每个景点与用户的匹配度
        from assessment import AttractionAssessor
        assessor = AttractionAssessor()
        
        scored_attractions = []
        for attraction in attractions:
            # 将数据库模型转换为字典
            attraction_data = {
                "id": attraction.id,
                "name": attraction.name,
                "city": attraction.city.name,
                "type": attraction.type,
                "address": attraction.address,
                "description": attraction.description,
                "opening_hours": attraction.opening_hours,
                "ticket_price": attraction.ticket_price,
                "recommended_time": attraction.recommended_time,
                "images": attraction.images,
                "overall_score": attraction.overall_score,
                "assessment_scores": attraction.assessment_scores,
                "assessment_summary": attraction.assessment_summary,
                "reviews": attraction.reviews
            }
            
            # 计算匹配度
            match_score = assessor.calculate_match_score(
                user_assessment.assessment_result,
                attraction_data
            )
            
            scored_attractions.append({
                **attraction_data,
                "match_score": match_score
            })
        
        # 4. 按匹配度排序，取前10个
        scored_attractions.sort(key=lambda x: x["match_score"], reverse=True)
        top_recommendations = scored_attractions[:10]
        
        return {"message": "推荐成功", "recommendations": top_recommendations}
    
    def _get_qualified_attractions(self, city_filter=None):
        """获取符合条件的景点"""
        query = Attraction.query.join(City)
        
        # 应用城市过滤
        if city_filter and city_filter.strip():
            query = query.filter(City.name == city_filter.strip())
        
        # 只选择评分较高的景点（综合评分 >= 7）
        query = query.filter(Attraction.overall_score >= 4.5)
        
        # 随机获取30个景点进行后续处理（避免处理过多数据）
        return query.order_by(db.func.random()).limit(30).all()
    
    def get_attractions_ranking(self, city_name, ranking_type="综合评分"):
        """获取景点排行榜"""
        # 1. 获取指定城市的景点
        city = City.query.filter_by(name=city_name).first()
        if not city:
            return {"message": "未找到该城市", "rankings": []}
        
        # 2. 根据指定类型排序
        query = Attraction.query.filter_by(city_id=city.id)
        
        # 映射排序类型到数据库字段
        type_mapping = {
            "综合评分": Attraction.overall_score,
            "风景指数": db.func.json_extract(Attraction.assessment_scores, "$.scenery"),
            "文化体验": db.func.json_extract(Attraction.assessment_scores, "$.culture"),
            "娱乐设施": db.func.json_extract(Attraction.assessment_scores, "$.facility"),
            "服务质量": db.func.json_extract(Attraction.assessment_scores, "$.service"),
            "性价比": db.func.json_extract(Attraction.assessment_scores, "$.value")
        }
        
        # 获取排序字段
        order_field = type_mapping.get(ranking_type, Attraction.overall_score)
        
        # 按评分降序排列
        attractions = query.order_by(db.desc(order_field)).limit(20).all()
        
        # 3. 转换为字典列表
        rankings = []
        for attraction in attractions:
            rankings.append({
                "id": attraction.id,
                "name": attraction.name,
                "city": city.name,
                "type": attraction.type,
                "description": attraction.description,
                "images": attraction.images,
                "overall_score": attraction.overall_score,
                "assessment_scores": attraction.assessment_scores
            })
        
        return {"message": "获取排行榜成功", "rankings": rankings}
