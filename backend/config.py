import os

# 数据库配置
DATABASE_URI = 'sqlite:///travel_recommender.db'

# 密钥配置
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_secret_key')  # 生产环境中应更换为安全的密钥

# API配置
API_PREFIX = '/api'
DEBUG = True
PORT = 5000

# DeepSeek API配置 (请替换为您自己的API密钥)
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'your_deepseek_api_key')
DEEPSEEK_API_URL = 'https://api.deepseek.com/v1/chat/completions'

# 爬虫配置
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
TIMEOUT = 10
RETRY_TIMES = 3
