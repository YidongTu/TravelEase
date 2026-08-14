from flask import Flask, request, jsonify, g
from flask_cors import CORS
import jwt
from datetime import datetime, timedelta
from functools import wraps
import json

# 导入模块
from config import SECRET_KEY, API_PREFIX, DEBUG, PORT, DATABASE_URI
from database import db, init_db, User, UserAssessment, City, Attraction
from scraper import AttractionScraper
from assessment import UserAssessmentAnalyzer, AttractionAssessor
from recommendation import RecommendationEngine

# 初始化Flask应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = SECRET_KEY

# 允许跨域请求
CORS(app)

# 初始化数据库
init_db(app)

# 初始化工具类
scraper = AttractionScraper()
user_analyzer = UserAssessmentAnalyzer()
attraction_assessor = AttractionAssessor()
recommendation_engine = RecommendationEngine()

# 认证装饰器
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # 从请求头获取token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': '认证令牌缺失'}), 401
        
        try:
            # 解码token
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
            
            if not current_user:
                return jsonify({'message': '无效的认证令牌'}), 401
                
            # 将当前用户存储在g对象中
            g.user = current_user
            
        except jwt.ExpiredSignatureError:
            return jsonify({'message': '认证令牌已过期'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': '无效的认证令牌'}), 401
            
        return f(*args, **kwargs)
    
    return decorated

# 路由：注册
@app.route(f'{API_PREFIX}/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # 验证数据
    if not all(k in data for k in ['name', 'email', 'password']):
        return jsonify({'message': '请提供完整的注册信息'}), 400
    
    # 检查邮箱是否已被注册
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': '该邮箱已被注册'}), 400
    
    # 创建新用户
    new_user = User(
        name=data['name'],
        email=data['email']
    )
    new_user.set_password(data['password'])
    
    # 保存到数据库
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'message': '注册成功',
        'user_id': new_user.id
    }), 201

# 路由：登录
@app.route(f'{API_PREFIX}/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # 验证数据
    if not all(k in data for k in ['email', 'password']):
        return jsonify({'message': '请提供邮箱和密码'}), 400
    
    # 查找用户
    user = User.query.filter_by(email=data['email']).first()
    
    # 验证密码
    if not user or not user.check_password(data['password']):
        return jsonify({'message': '邮箱或密码不正确'}), 401
    
    # 生成JWT令牌（有效期7天）
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }, SECRET_KEY, algorithm="HS256")
    
    return jsonify({
        'message': '登录成功',
        'token': token,
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'has_completed_assessment': user.has_completed_assessment
        }
    }), 200

# 路由：验证token
@app.route(f'{API_PREFIX}/auth/verify', methods=['GET'])
@token_required
def verify_token():
    return jsonify({
        'message': '令牌有效',
        'user': {
            'id': g.user.id,
            'name': g.user.name,
            'email': g.user.email,
            'has_completed_assessment': g.user.has_completed_assessment
        }
    }), 200

# 路由：提交兴趣评估
@app.route(f'{API_PREFIX}/assessment', methods=['POST'])
@token_required
def submit_assessment():
    data = request.get_json()
    
    # 分析用户答案
    assessment_result = user_analyzer.analyze_answers(data)
    
    # 保存评估结果
    user_assessment = UserAssessment.query.filter_by(user_id=g.user.id).first()
    
    if user_assessment:
        # 更新现有评估
        user_assessment.answers = data
        user_assessment.assessment_result = assessment_result
        user_assessment.updated_at = datetime.utcnow()
    else:
        # 创建新评估
        user_assessment = UserAssessment(
            user_id=g.user.id,
            answers=data,
            assessment_result=assessment_result
        )
        db.session.add(user_assessment)
    
    # 更新用户状态
    g.user.has_completed_assessment = True
    
    # 保存到数据库
    db.session.commit()
    
    return jsonify({
        'message': '兴趣评估已提交',
        'assessment_result': assessment_result
    }), 200

# 路由：获取城市景点
@app.route(f'{API_PREFIX}/attractions', methods=['GET'])
@token_required
def get_attractions():
    city_name = request.args.get('city', '')
    
    if not city_name:
        return jsonify({'message': '请提供城市名称'}), 400
    
    # 检查数据库中是否已有该城市的景点
    city = City.query.filter_by(name=city_name).first()
    
    if city and city.attractions:
        # 从数据库获取
        attractions = city.attractions
    else:
        # 爬取新数据
        scraped_attractions = scraper.get_attractions_by_city(city_name)
        
        if not scraped_attractions:
            return jsonify({'message': f'未找到{city_name}的景点数据'}), 404
        
        # 如果城市不存在，则创建
        if not city:
            city = City(name=city_name)
            db.session.add(city)
            db.session.commit()
        
        # 保存景点数据
        attractions = []
        for attr_data in scraped_attractions:
            # 评估景点
            assessed_attr = attraction_assessor.assess_attraction(attr_data)
            
            # 创建景点记录
            attraction = Attraction(
                city_id=city.id,
                name=assessed_attr['name'],
                address=assessed_attr.get('address', ''),
                description=assessed_attr.get('description', ''),
                type=assessed_attr.get('type', ''),
                opening_hours=assessed_attr.get('opening_hours', ''),
                ticket_price=assessed_attr.get('ticket_price', ''),
                recommended_time=assessed_attr.get('recommended_time', ''),
                images=assessed_attr.get('images', []),
                overall_score=assessed_attr.get('overall_score', 0),
                assessment_scores=assessed_attr.get('assessment_scores', {}),
                assessment_summary=assessed_attr.get('assessment_summary', ''),
                reviews=assessed_attr.get('reviews', [])
            )
            
            db.session.add(attraction)
            attractions.append(attraction)
        
        db.session.commit()
    
    # 准备返回数据
    result = []
    for attr in attractions:
        # 如果用户已完成评估，计算匹配度
        match_score = None
        if g.user.has_completed_assessment:
            user_assessment = UserAssessment.query.filter_by(user_id=g.user.id).first()
            if user_assessment and user_assessment.assessment_result:
                attr_data = {
                    "name": attr.name,
                    "type": attr.type,
                    "assessment_scores": attr.assessment_scores
                }
                match_score = attraction_assessor.calculate_match_score(
                    user_assessment.assessment_result,
                    attr_data
                )
        
        result.append({
            "id": attr.id,
            "name": attr.name,
            "city": city.name,
            "type": attr.type,
            "address": attr.address,
            "description": attr.description,
            "images": attr.images,
            "overall_score": attr.overall_score,
            "match_score": match_score
        })
    
    return jsonify({
        'message': f'成功获取{city_name}的景点数据',
        'attractions': result
    }), 200

# 路由：获取景点详情
@app.route(f'{API_PREFIX}/attractions/<attraction_id>', methods=['GET'])
@token_required
def get_attraction_details(attraction_id):
    # 查找景点
    attraction = Attraction.query.filter_by(id=attraction_id).first()
    
    if not attraction:
        return jsonify({'message': '未找到该景点'}), 404
    
    # 获取城市名称
    city = City.query.filter_by(id=attraction.city_id).first()
    city_name = city.name if city else ''
    
    # 如果用户已完成评估，计算匹配度
    match_score = None
    if g.user.has_completed_assessment:
        user_assessment = UserAssessment.query.filter_by(user_id=g.user.id).first()
        if user_assessment and user_assessment.assessment_result:
            attr_data = {
                "name": attraction.name,
                "type": attraction.type,
                "assessment_scores": attraction.assessment_scores
            }
            match_score = attraction_assessor.calculate_match_score(
                user_assessment.assessment_result,
                attr_data
            )
    
    # 准备返回数据
    return jsonify({
        'message': '成功获取景点详情',
        'attraction': {
            "id": attraction.id,
            "name": attraction.name,
            "city": city_name,
            "address": attraction.address,
            "description": attraction.description,
            "type": attraction.type,
            "opening_hours": attraction.opening_hours,
            "ticket_price": attraction.ticket_price,
            "recommended_time": attraction.recommended_time,
            "images": attraction.images,
            "overall_score": attraction.overall_score,
            "assessment_scores": attraction.assessment_scores,
            "assessment_summary": attraction.assessment_summary,
            "reviews": attraction.reviews,
            "match_score": match_score
        }
    }), 200

# 路由：获取景点排行榜
@app.route(f'{API_PREFIX}/rankings', methods=['GET'])
@token_required
def get_attractions_ranking():
    city_name = request.args.get('city', '')
    ranking_type = request.args.get('type', '综合评分')
    
    if not city_name:
        return jsonify({'message': '请提供城市名称'}), 400
    
    # 获取排行榜
    result = recommendation_engine.get_attractions_ranking(city_name, ranking_type)
    
    return jsonify(result), 200 if result['rankings'] else 404

# 路由：获取推荐景点
@app.route(f'{API_PREFIX}/recommendations', methods=['GET'])
@token_required
def get_recommendations():
    city_filter = request.args.get('city', '')
    
    # 获取推荐
    result = recommendation_engine.get_recommendations(g.user.id, city_filter)
    
    return jsonify(result), 200

# 启动应用
if __name__ == '__main__':
    app.run(debug=DEBUG, port=PORT)
