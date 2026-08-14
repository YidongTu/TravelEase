from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import uuid

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    has_completed_assessment = db.Column(db.Boolean, default=False)
    
    # 关联
    assessment = db.relationship('UserAssessment', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserAssessment(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    answers = db.Column(db.JSON, nullable=False)  # 存储用户的原始答案
    assessment_result = db.Column(db.JSON)  # 存储评估结果
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class City(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    attractions = db.relationship('Attraction', backref='city', lazy=True, cascade='all, delete-orphan')

class Attraction(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    city_id = db.Column(db.String(36), db.ForeignKey('city.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(500))
    description = db.Column(db.Text)
    type = db.Column(db.String(100))  # 景点类型
    opening_hours = db.Column(db.String(500))  # 开放时间
    ticket_price = db.Column(db.String(200))  # 门票价格
    recommended_time = db.Column(db.String(200))  # 建议游玩时间
    images = db.Column(db.JSON)  # 图片URL列表
    overall_score = db.Column(db.Float)  # 综合评分
    assessment_scores = db.Column(db.JSON)  # 各项评分
    assessment_summary = db.Column(db.Text)  # 评估总结
    reviews = db.Column(db.JSON)  # 游客评价
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db(app):
    """初始化数据库"""
    db.init_app(app)
    
    # 创建所有表
    with app.app_context():
        db.create_all()
