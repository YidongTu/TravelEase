# TravelEase - 基于AI算法的智能旅游推荐系统

> 🏆 竞赛项目 | 2025.09 - 2025.10

## 📋 项目简介

TravelEase 是一套基于 **AI多因子加权评估算法** 的智能旅游推荐系统，核心围绕景点与游览时机的智能推荐展开。系统综合考虑实时客流拥挤度、天气舒适度、历史评价情感倾向、游览耗时等多个维度，通过加权评估模型为游客智能推荐最佳游览景点与出行时段。

项目覆盖从用户兴趣评估、景点搜索、客流监测、天气展示到个性化推荐、用户收藏的完整功能闭环，为旅游者提供一站式智能出行决策支持。

---

## ✨ 核心特性

### 🧠 AI 智能推荐
- **多因子加权评估模型**：客流拥挤度(30%) + 天气舒适度(25%) + 评价情感得分(25%) + 游览效率(20%)
- **用户兴趣画像**：通过问卷评估构建用户偏好向量，支持6大维度特征量化
- **匹配度计算**：景点特征与用户偏好的多维余弦匹配，输出Top10个性化推荐
- **景点排行榜**：支持综合评分、风景指数、文化体验、娱乐设施、服务质量、性价比6种维度排序

### 🕷️ 智能爬虫系统
- **三级数据获取策略**：数据库缓存 → 网络爬虫 → 模拟数据回退
- 携程景点数据爬取（支持20+热门城市）
- 详情页图文信息提取 + 评论情感分析
- 失败自动降级机制，保障推荐系统高可用

### 📊 数据可视化
- 景点评分雷达图与分布展示
- 客流趋势与天气舒适度图表
- 用户兴趣画像可视化分析

### 🔐 用户系统
- JWT Token 认证机制（7天有效期）
- 用户密码 bcrypt 安全加密存储
- 兴趣评估状态追踪
- 景点收藏与浏览历史

---

## 🛠️ 技术栈

| 层级 | 技术选型 |
|------|----------|
| **后端** | Node.js / Express、RESTful API、bcrypt、cheerio |
| **AI算法** | 多因子加权评估模型、情感分析、特征向量匹配 |
| **数据库** | MySQL（8张核心表）、SQLAlchemy ORM |
| **前端** | HTML5、Tailwind CSS、Chart.js、原生JavaScript |
| **爬虫** | 请求重试机制、Selenium动态渲染、BeautifulSoup解析 |
| **认证** | JWT Token、Werkzeug 安全加密 |

---

## 📁 项目结构

```
TravelEase/
├── backend/                    # 后端服务
│   ├── app.py                  # Flask应用入口 + RESTful API路由
│   ├── config.py               # 全局配置（数据库、密钥、爬虫参数）
│   ├── database.py             # 数据模型定义（8张表）
│   ├── assessment.py           # 用户兴趣评估 + 景点评估器
│   ├── recommendation.py       # 推荐引擎（匹配算法 + 排行榜）
│   ├── scraper.py              # 爬虫调度器（三级获取策略）
│   └── 爬虫.py                 # 携程景点爬虫核心（Selenium + BS4）
│
├── frontend/                   # 前端页面
│   ├── index.html              # 登录页
│   ├── register.html           # 注册页
│   ├── interest_assessment.html # 兴趣评估问卷
│   ├── city_attractions.html   # 城市景点列表
│   ├── attraction_details.html # 景点详情页
│   ├── attractions_ranking.html # 景点排行榜
│   ├── recommendations.html    # 个性化推荐页
│   ├── algorithm_flows.html    # 算法流程图展示
│   ├── css/style.css           # 样式文件
│   ├── js/script.js            # 前端交互逻辑
│   └── images/                 # 算法流程SVG图
│
├── instance/
│   └── travel_recommender.db   # SQLite数据库（可切换MySQL）
└── ctrip_crawler.log           # 爬虫运行日志
```

---

## 🗄️ 数据库设计

共设计 **8张核心数据表**，为推荐算法提供多维数据支撑：

| 表名 | 说明 | 核心字段 |
|------|------|----------|
| `user` | 用户表 | id, name, email, password_hash, has_completed_assessment |
| `user_assessment` | 用户评估表 | user_id, answers(JSON), assessment_result(JSON) |
| `city` | 城市表 | id, name |
| `attraction` | 景点表 | city_id, name, address, type, opening_hours, ticket_price, overall_score, assessment_scores(JSON), reviews(JSON) |
| `reviews` | 评价表 | attraction_id, user_id, rating, content, sentiment |
| `crowd_flow` | 客流表 | attraction_id, datetime, crowd_level, forecast_value |
| `weather` | 天气表 | city_id, date, temperature, comfort_index, weather_desc |
| `favorites` | 收藏表 | user_id, attraction_id, created_at |

---

## 🧮 核心算法

### 1. 多因子加权推荐指数模型

```python
推荐指数 = 客流拥挤度 × 30%
        + 天气舒适度 × 25%
        + 评价情感得分 × 25%
        + 游览效率得分 × 20%
```

### 2. 用户兴趣特征提取

通过6道问卷题目量化用户8大特征维度：
- 自然景观偏好 / 文化历史偏好 / 城市观光偏好
- 冒险体验偏好 / 休闲放松偏好 / 美食偏好
- 拥挤容忍度 / 价格敏感度

归一化至 **0-10分制**，取Top3偏好作为用户核心标签。

### 3. 用户-景点匹配度计算

```python
匹配度 = 特征匹配度(70%) + 类型匹配度(30%)

特征匹配度 = Σ(1 - |用户特征ᵢ - 景点特征ᵢ|) / n
类型匹配度 = 用户偏好类型 ∩ 景点标签关键词
```

### 4. 三级爬虫数据获取策略

```
请求 → ① 数据库缓存（命中直接返回）
        ↓ 未命中
     ② 网络爬虫（携程景点页 → 详情页 → 评论提取）
        ↓ 爬取失败
     ③ 模拟数据回退（内置热门城市景点模板库）
```

---

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 14+（如使用Node.js版本）
- MySQL 5.7+ / SQLite（默认）
- Chrome Browser（Selenium爬虫需要）

### 1. 克隆项目

```bash
git clone https://github.com/your-username/TravelEase.git
cd TravelEase
```

### 2. 安装依赖

```bash
# Python后端依赖
pip install flask flask-sqlalchemy flask-cors pyjwt werkzeug
pip install requests beautifulsoup4 selenium pandas webdriver-manager
```

### 3. 配置环境变量

编辑 `backend/config.py`：

```python
# 数据库（MySQL示例）
DATABASE_URI = 'mysql+pymysql://username:password@localhost:3306/travelease'

# JWT密钥
SECRET_KEY = 'your_secure_secret_key'

# DeepSeek API（用于AI生成评估描述，可选）
DEEPSEEK_API_KEY = 'your_deepseek_api_key'
```

### 4. 启动后端服务

```bash
cd backend
python app.py
# 服务启动于 http://localhost:5000
```

### 5. 访问前端页面

直接用浏览器打开 `frontend/index.html`，或使用本地静态服务器：

```bash
cd frontend
python -m http.server 8080
# 访问 http://localhost:8080
```

---

## 🔌 API 接口一览

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/auth/register` | 用户注册 | ❌ |
| POST | `/api/auth/login` | 用户登录 | ❌ |
| GET | `/api/auth/verify` | 验证Token | ✅ |
| POST | `/api/assessment` | 提交兴趣评估 | ✅ |
| GET | `/api/attractions?city=北京` | 获取城市景点列表 | ✅ |
| GET | `/api/attractions/:id` | 获取景点详情 | ✅ |
| GET | `/api/rankings?city=北京` | 获取景点排行榜 | ✅ |
| GET | `/api/recommendations?city=` | 获取个性化推荐 | ✅ |

---

## 📸 页面流程

```
登录/注册 → 兴趣评估问卷（构建用户画像）
                ↓
        城市景点搜索/浏览
        ↙        ↘
  景点详情页    景点排行榜
        ↘        ↙
          个性化推荐（Top10）
```

---

## 🎯 项目亮点

1. **AI评估算法**：自研多因子加权模型，覆盖客流、天气、情感、效率4大核心维度
2. **高可用爬虫架构**：三级数据获取策略，网络异常时自动降级，推荐服务零中断
3. **完整功能闭环**：注册登录 → 兴趣评估 → 景点浏览 → 详情查看 → 排行分析 → 个性推荐 → 收藏管理
4. **RESTful API设计**：标准HTTP状态码 + JWT认证，前后端完全分离
5. **可视化算法展示**：内置算法流程图页面，直观展示推荐引擎内部逻辑

---

## 📝 License

MIT License - 仅用于竞赛项目展示与学习交流。
