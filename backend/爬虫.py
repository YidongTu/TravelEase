import requests
from bs4 import BeautifulSoup
import csv
import time
import random
import re
import json
import os
from urllib.parse import quote, urljoin
import logging
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ctrip_crawler.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('CtripCrawler')

class CtripScenicSpotCrawler:
    def __init__(self, city="沈阳", keyword="", max_pages=10, max_concurrency=5, proxies=None):
        """
        携程景点爬虫
        
        :param city: 城市名称
        :param keyword: 搜索关键词
        :param max_pages: 最大爬取页数
        :param max_concurrency: 最大并发数（用于详情页爬取）
        :param proxies: 代理列表，格式: ["http://ip:port", "https://ip:port"]
        """
        self.city = city
        self.keyword = keyword
        self.max_pages = max_pages
        self.max_concurrency = max_concurrency
        self.scenic_spots = []
        self.proxies = proxies or []
        
        # 携程城市编码映射
        self.city_codes = {
            "北京": "t3", "上海": "t2", "广州": "t152", "深圳": "t153",
            "杭州": "t17", "成都": "t104", "武汉": "t105", "南京": "t11",
            "贵阳": "t1147", "西安": "t7", "重庆": "t106", "苏州": "t14",
            "沈阳": "t155", "大连": "t156", "青岛": "t161", "厦门": "t160",
            "天津": "t159", "长沙": "t148", "郑州": "t157", "昆明": "t154",
            "哈尔滨": "t158", "长春": "t178", "福州": "t180", "南宁": "t179",
            "全国": "all"
        }
        
        self.base_url = "https://you.ctrip.com"
        
        # 预定义User-Agent列表
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
            "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
        ]
        
        # 初始化requests会话，增加重试机制
        self.session = self._init_session()
        
        # 初始化Selenium浏览器
        self.driver = self.init_selenium_driver()
    
    def _init_session(self):
        """初始化带重试机制的requests会话"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def init_selenium_driver(self):
        """初始化Selenium浏览器驱动"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(f"user-agent={random.choice(self.user_agents)}")
            
            # 禁用图片加载提高速度
            prefs = {"profile.managed_default_content_settings.images": 2}
            chrome_options.add_experimental_option("prefs", prefs)
            
            # 如果有代理，配置代理
            if self.proxies:
                proxy = random.choice(self.proxies)
                chrome_options.add_argument(f'--proxy-server={proxy}')
            
            driver = webdriver.Chrome(
                executable_path=ChromeDriverManager().install(),
                options=chrome_options
            )
            logger.info("Selenium浏览器初始化成功")
            return driver
        except Exception as e:
            logger.error(f"浏览器初始化失败: {str(e)}")
            return None
    
    def get_random_header(self):
        """获取随机请求头"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': 'https://you.ctrip.com/',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def get_page(self, url, max_retries=3):
        """获取页面内容，带重试机制"""
        for attempt in range(max_retries):
            try:
                headers = self.get_random_header()
                kwargs = {'headers': headers, 'timeout': 15}
                
                # 随机选择代理
                if self.proxies and attempt > 0:  # 失败后再使用代理
                    proxy = random.choice(self.proxies)
                    kwargs['proxies'] = {'http': proxy, 'https': proxy}
                
                response = self.session.get(url, **kwargs)
                if response.status_code == 200:
                    return response.text
                else:
                    logger.warning(f"请求失败: {url}, 状态码: {response.status_code}, 尝试次数: {attempt+1}")
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(1, 3))
            except Exception as e:
                logger.error(f"请求异常: {url}, 错误: {str(e)}, 尝试次数: {attempt+1}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(1, 3))
        
        return None
    
    def get_page_with_selenium(self, url, max_retries=2):
        """使用Selenium获取页面内容，带重试机制"""
        if not self.driver:
            return None
        
        for attempt in range(max_retries):
            try:
                self.driver.get(url)
                # 等待页面加载完成，使用更通用的等待条件
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                # 额外等待动态内容加载
                time.sleep(random.uniform(1, 2))
                return self.driver.page_source
            except Exception as e:
                logger.error(f"Selenium获取页面失败: {url}, 错误: {str(e)}, 尝试次数: {attempt+1}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(2, 4))
        
        return None
    
    def parse_list_page(self, html, page_url):
        """解析景点列表页"""
        scenic_spots = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 查找所有景点卡片，增加更多可能的类名
            spot_cards = soup.find_all('div', class_=lambda x: x and any(cls in x for cls in 
                ['sightItemCard_box', 'card-item', 'sight_item', 'list_item', 'poi-item']))
            
            if not spot_cards:
                logger.warning(f"未找到景点卡片，页面结构可能已变化: {page_url}")
                # 保存错误页面用于调试
                with open(f"error_page_{int(time.time())}.html", "w", encoding="utf-8") as f:
                    f.write(html)
                return scenic_spots
            
            logger.info(f"找到 {len(spot_cards)} 个景点卡片")
            
            for card in spot_cards:
                try:
                    spot_info = self.parse_spot_card(card)
                    if spot_info:
                        scenic_spots.append(spot_info)
                except Exception as e:
                    logger.error(f"解析单个景点卡片失败: {str(e)}")
                    continue
            
        except Exception as e:
            logger.error(f"解析列表页失败: {str(e)}")
        
        return scenic_spots
    
    def parse_spot_card(self, card):
        """解析单个景点卡片"""
        try:
            # 景点名称 - 增加更多解析路径
            name_elem = None
            name_selectors = [
                card.find('div', class_=lambda x: x and 'titleModule_name' in x),
                card.find('dt', class_='ellipsis'),
                card.find('h3', class_=lambda x: x and 'name' in x),
                card.find('div', class_=lambda x: x and 'poi-name' in x)
            ]
            
            for selector in name_selectors:
                if selector:
                    name_elem = selector.find('a')
                    if name_elem:
                        break
            
            name = name_elem.text.strip() if name_elem else "未知"
            
            # 景点链接
            link = name_elem.get('href') if name_elem else ""
            if link and not link.startswith('http'):
                link = urljoin(self.base_url, link)
            
            # 景点图片获取逻辑
            image_elem = None
            image_containers = [
                card.find('img', class_=lambda x: x and ('image' in x or 'img' in x or 'photo' in x)),
                card.find('div', class_=lambda x: x and ('image' in x or 'img' in x or 'photo' in x)),
                card.find('div', class_=lambda x: x and 'pic' in x)
            ]
            
            for container in image_containers:
                if container:
                    if container.name == 'img':
                        image_elem = container
                    else:
                        image_elem = container.find('img')
                    if image_elem:
                        break

            image_url = ""
            if image_elem:
                # 检查是否有data-src（懒加载）
                image_url = image_elem.get('data-src', '') or image_elem.get('src', '') or image_elem.get('data-original', '')
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(self.base_url, image_url)

            # 清理可能的参数（保留基础图片路径）
            if '?' in image_url:
                image_url = image_url.split('?')[0]
            
            # 评分
            rating_elem = None
            rating_selectors = [
                card.find('span', class_=lambda x: x and 'commentInfoModule_comment-score_value' in x),
                card.find('span', class_='comment_score'),
                card.find('div', class_=lambda x: x and 'rating' in x)
            ]
            
            for selector in rating_selectors:
                if selector:
                    rating_elem = selector
                    break
            
            rating = rating_elem.text.strip() if rating_elem else "0.0"
            
            # 评论数量
            comment_elem = None
            comment_selectors = [
                card.find('span', string=lambda x: x and '条点评' in x),
                card.find('span', class_='comment_count'),
                card.find('div', string=lambda x: x and '点评' in x)
            ]
            
            for selector in comment_selectors:
                if selector:
                    comment_elem = selector
                    break
            
            comment_text = comment_elem.text.strip() if comment_elem else "0条点评"
            comment_count = re.search(r'(\d+)', comment_text)
            comment_count = comment_count.group(1) if comment_count else "0"
            
            # 地址信息
            address_elems = []
            address_selectors = [
                card.find_all('span', class_=lambda x: x and 'distanceView_desc-text' in x),
                card.find('div', class_='address') if card.find('div', class_='address') else []
            ]
            
            for selector in address_selectors:
                if selector:
                    if isinstance(selector, list):
                        address_elems = selector
                    else:
                        address_elems = selector.find_all('span')
                    if address_elems:
                        break
            
            address_parts = [elem.text.strip() for elem in address_elems if elem.text.strip()]
            address = " · ".join(address_parts) if address_parts else "未知"
            
            # 价格
            price_elem = None
            price_selectors = [
                card.find('span', class_=lambda x: x and 'priceView_real-price-text' in x),
                card.find('div', class_='price') if card.find('div', class_='price') else None,
                card.find('span', class_=lambda x: x and 'price' in x)
            ]
            
            for selector in price_selectors:
                if selector:
                    if selector.name == 'span':
                        price_elem = selector
                    else:
                        price_elem = selector.find('span')
                    if price_elem:
                        break
            
            price = price_elem.text.strip() if price_elem else "免费"
            
            # 如果显示"免费"，则价格为0
            if "免费" in price:
                price = "0"
            
            # 景点等级（如4A）
            level_elem = None
            level_selectors = [
                card.find('span', class_=lambda x: x and 'titleModule_level-text' in x),
                card.find('span', class_='level-text'),
                card.find('span', string=lambda x: x and ('A' in x or '级' in x))
            ]
            
            for selector in level_selectors:
                if selector:
                    level_elem = selector
                    break
            
            level = level_elem.text.strip() if level_elem else ""
            
            # 热度评分
            heat_elem = card.find('span', class_=lambda x: x and 'commentInfoModule_heat-score_value' in x)
            heat_score = heat_elem.text.strip() if heat_elem else "0.0"
            
            # 标签信息
            tag_elems = []
            tag_selectors = [
                card.find_all('span', class_=lambda x: x and 'rankInfoModule_tag_text' in x),
                card.find_all('div', class_=lambda x: x and 'product-tips' in x),
                card.find_all('span', class_=lambda x: x and 'tag' in x)
            ]
            
            for selector in tag_selectors:
                if selector:
                    tag_elems = selector
                    break
            
            tags = [tag.text.strip() for tag in tag_elems] if tag_elems else []
            
            # 特色标签（如随时退、可订明日等）
            feature_elems = card.find_all('span', class_=lambda x: x and 'otherTagsModule_tag-text' in x)
            features = [feature.text.strip() for feature in feature_elems] if feature_elems else []
            
            spot_info = {
                "name": name,
                "rating": float(rating) if rating.replace('.', '', 1).isdigit() else 0.0,
                "comment_count": int(comment_count) if comment_count.isdigit() else 0,
                "address": address,
                "price": price,
                "level": level,
                "heat_score": float(heat_score) if heat_score.replace('.', '', 1).isdigit() else 0.0,
                "tags": tags,
                "features": features,
                "image_url": image_url,
                "detail_url": link,
                "city": self.city
            }
            
            return spot_info
            
        except Exception as e:
            logger.error(f"解析景点卡片详细失败: {str(e)}")
            return None
    
    def get_detail_info(self, spot_info):
        """获取景点详情页信息"""
        if not spot_info.get("detail_url"):
            spot_info.update({
                "open_time": "未知",
                "phone": "未知",
                "description": "暂无简介"
            })
            return spot_info
        
        try:
            # 尝试使用requests获取详情页
            html = self.get_page(spot_info["detail_url"])
            if not html:
                # 如果requests失败，使用Selenium
                logger.info(f"尝试使用Selenium获取详情页: {spot_info['detail_url']}")
                html = self.get_page_with_selenium(spot_info["detail_url"])
                if not html:
                    spot_info.update({
                        "open_time": "获取失败",
                        "phone": "获取失败",
                        "description": "获取失败"
                    })
                    return spot_info
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 开放时间
            open_time = "未知"
            open_time_selectors = [
                soup.find('dd', class_='open-time'),
                soup.find('div', string=lambda x: x and '开放时间' in x),
                soup.find('div', class_=lambda x: x and 'open-time' in x)
            ]
            
            for selector in open_time_selectors:
                if selector:
                    if selector.name == 'dd':
                        open_time = selector.text.strip()
                    else:
                        next_sibling = selector.find_next_sibling()
                        open_time = next_sibling.text.strip() if next_sibling else "未知"
                    break
            
            # 联系电话
            phone = "未知"
            phone_selectors = [
                soup.find('dd', class_='tel'),
                soup.find('div', string=lambda x: x and '电话' in x),
                soup.find('div', class_=lambda x: x and 'contact' in x)
            ]
            
            for selector in phone_selectors:
                if selector:
                    if selector.name == 'dd':
                        phone = selector.text.strip()
                    else:
                        next_sibling = selector.find_next_sibling()
                        phone = next_sibling.text.strip() if next_sibling else "未知"
                    break
            
            # 景区简介
            description = "暂无简介"
            desc_selectors = [
                soup.find('div', class_='intro'),
                soup.find('div', class_='detail-content'),
                soup.find('div', class_='text'),
                soup.find('div', class_=lambda x: x and 'description' in x)
            ]
            
            for selector in desc_selectors:
                if selector:
                    description = selector.text.strip()
                    break
            
            # 如果简介太长，截取前200字符
            if len(description) > 200:
                description = description[:200] + "..."
            
            # 更新景点信息
            spot_info.update({
                "open_time": open_time,
                "phone": phone,
                "description": description
            })
            
        except Exception as e:
            logger.error(f"获取详情页信息失败 {spot_info['name']}: {str(e)}")
            spot_info.update({
                "open_time": "解析错误",
                "phone": "解析错误",
                "description": "解析错误"
            })
        
        # 随机延迟，避免请求过快
        time.sleep(random.uniform(0.5, 1.5))
        return spot_info
    
    def determine_max_pages(self, html):
        """从页面中解析实际最大页数"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 尝试解析分页信息
            pagination = soup.find('div', class_='pagination') or soup.find('div', class_='pager')
            if pagination:
                # 查找最大页码
                page_links = pagination.find_all('a', href=lambda x: x and 'p' in x)
                if page_links:
                    last_page = page_links[-1].text
                    if last_page and last_page.isdigit():
                        return int(last_page)
            
            # 尝试从文本中解析
            page_info = soup.find('span', class_='pagination-info') or soup.find('div', class_='page-info')
            if page_info:
                match = re.search(r'1-(\d+)/(\d+)', page_info.text)
                if match:
                    return int(match.group(2))
            
            # 默认返回最大页数
            return self.max_pages
        except Exception as e:
            logger.warning(f"解析最大页数失败: {str(e)}")
            return self.max_pages
    
    def crawl_city_spots(self, city=None, keyword=None):
        """爬取指定城市的景点信息"""
        if city:
            self.city = city
        if keyword is not None:
            self.keyword = keyword
        
        city_code = self.city_codes.get(self.city)
        if not city_code:
            logger.error(f"未找到城市 {self.city} 的编码")
            return []
        
        logger.info(f"开始爬取 {self.city} 的景点信息...")
        start_time = time.time()
        
        # 第一步：获取第一页确定实际页数
        if self.keyword:
            first_page_url = f"{self.base_url}/sight/{city_code}/s0-k{quote(self.keyword)}-p1.html"
        else:
            first_page_url = f"{self.base_url}/sight/{city_code}/s0-p1.html"
        
        logger.info(f"获取第一页: {first_page_url}")
        first_page_html = self.get_page(first_page_url)
        
        if not first_page_html:
            logger.error("无法获取第一页，尝试使用Selenium")
            first_page_html = self.get_page_with_selenium(first_page_url)
            if not first_page_html:
                logger.error("Selenium也无法获取第一页，爬取终止")
                return []
        
        # 确定实际最大页数
        actual_max_pages = self.determine_max_pages(first_page_html)
        actual_max_pages = min(actual_max_pages, self.max_pages)
        logger.info(f"实际可爬取页数: {actual_max_pages}")
        
        # 生成所有要爬取的页面URL
        list_urls = []
        for page in range(1, actual_max_pages + 1):
            if self.keyword:
                url = f"{self.base_url}/sight/{city_code}/s0-k{quote(self.keyword)}-p{page}.html"
            else:
                url = f"{self.base_url}/sight/{city_code}/s0-p{page}.html"
            list_urls.append(url)
        
        # 第二步：爬取所有列表页
        logger.info(f"开始爬取 {len(list_urls)} 页列表数据...")
        all_spots = []
        for i, url in enumerate(list_urls):
            # 先尝试requests获取
            html = self.get_page(url)
            if not html:
                logger.info(f"尝试使用Selenium获取第{i+1}页: {url}")
                html = self.get_page_with_selenium(url)
            
            if html:
                spots = self.parse_list_page(html, url)
                all_spots.extend(spots)
                logger.info(f"第{i+1}页解析完成，获取{len(spots)}个景点")
            else:
                logger.warning(f"第{i+1}页获取失败")
            
            # 页面间延迟，随机增加延迟时间避免被识别
            if i < len(list_urls) - 1:
                delay = random.uniform(2, 5)
                logger.info(f"等待 {delay:.1f}秒后继续...")
                time.sleep(delay)
        
        logger.info(f"共获取 {len(all_spots)} 个景点基本信息")
        
        # 去重处理
        unique_spots = []
        seen_names = set()
        for spot in all_spots:
            if spot['name'] not in seen_names:
                seen_names.add(spot['name'])
                unique_spots.append(spot)
        logger.info(f"去重后剩余 {len(unique_spots)} 个景点")
        all_spots = unique_spots
        
        # 第三步：获取详情页信息
        logger.info("开始获取详情页信息...")
        for i, spot in enumerate(all_spots):
            self.get_detail_info(spot)
            if (i + 1) % 5 == 0:
                logger.info(f"已完成 {i+1}/{len(all_spots)} 个景点详情获取")
        
        self.scenic_spots = all_spots
        
        elapsed_time = time.time() - start_time
        logger.info(f"爬取完成！共获取 {len(self.scenic_spots)} 个景点信息，耗时 {elapsed_time:.2f} 秒")
        
        return self.scenic_spots
    
    def save_to_json(self, filename=None):
        """保存数据到JSON文件"""
        if not self.scenic_spots:
            logger.warning("没有数据可保存")
            return False
        
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"ctrip_scenic_spots_{self.city}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                # 确保数据可序列化
                serializable_data = []
                for spot in self.scenic_spots:
                    serializable_spot = spot.copy()
                    # 确保所有值都是可序列化的
                    for key, value in serializable_spot.items():
                        if isinstance(value, (set,)):
                            serializable_spot[key] = list(value)
                    serializable_data.append(serializable_spot)
                
                json.dump(serializable_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"数据已保存到 {filename}")
            return True
        except Exception as e:
            logger.error(f"保存JSON文件失败: {str(e)}")
            return False
    
    def save_to_csv(self, filename=None):
        """保存数据到CSV文件"""
        if not self.scenic_spots:
            logger.warning("没有数据可保存")
            return False
        
        if not filename:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"ctrip_scenic_spots_{self.city}_{timestamp}.csv"
        
        try:
            # 创建DataFrame
            data = []
            for spot in self.scenic_spots:
                data.append({
                    "城市": spot.get("city", ""),
                    "景点名称": spot.get("name", ""),
                    "评分": spot.get("rating", 0),
                    "评论数量": spot.get("comment_count", 0),
                    "热度评分": spot.get("heat_score", 0),
                    "景点等级": spot.get("level", ""),
                    "地址": spot.get("address", ""),
                    "价格": spot.get("price", ""),
                    "开放时间": spot.get("open_time", ""),
                    "联系电话": spot.get("phone", ""),
                    "标签": "|".join(spot.get("tags", [])),
                    "特色服务": "|".join(spot.get("features", [])),
                    "景区简介": spot.get("description", ""),
                    "详情页链接": spot.get("detail_url", ""),
                    "图片链接": spot.get("image_url", "")
                })
            
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            
            logger.info(f"数据已保存到 {filename}")
            return True
        except Exception as e:
            logger.error(f"保存CSV文件失败: {str(e)}")
            return False
    
    def display_results(self, limit=10):
        """显示爬取结果"""
        if not self.scenic_spots:
            logger.warning("没有数据可显示")
            return
        
        print(f"\n=== {self.city} 景点信息（前{limit}个）===")
        for i, spot in enumerate(self.scenic_spots[:limit]):
            print(f"\n{i+1}. {spot['name']}")
            print(f"   评分: {spot['rating']} | 评论: {spot['comment_count']}条 | 热度: {spot['heat_score']}")
            print(f"   等级: {spot['level']} | 价格: {spot['price']}元")
            print(f"   地址: {spot['address']}")
            print(f"   开放时间: {spot.get('open_time', '未知')}")
            print(f"   电话: {spot.get('phone', '未知')}")
            print(f"   标签: {', '.join(spot['tags'])}")
            print(f"   特色: {', '.join(spot['features'])}")
            print(f"   简介: {spot.get('description', '暂无简介')[:100]}...")
            print(f"   详情页: {spot['detail_url']}")
    
    def close(self):
        """关闭资源"""
        if self.session:
            self.session.close()
        if self.driver:
            self.driver.quit()
            logger.info("Selenium浏览器已关闭")

# 使用示例
def main():
    # 可以添加代理列表，格式: ["http://ip:port", "https://ip:port"]
    proxies = []
    
    # 创建爬虫实例
    crawler = CtripScenicSpotCrawler(
        city="沈阳",           # 要爬取的城市
        keyword="",            # 搜索关键词（可选）
        max_pages=10,          # 爬取页数
        proxies=proxies        # 代理列表（可选）
    )
    
    try:
        # 执行爬取
        spots = crawler.crawl_city_spots()
        
        if spots:
            # 显示结果
            crawler.display_results(limit=5)
            
            # 保存结果
            crawler.save_to_json()
            crawler.save_to_csv()
            
            # 统计信息
            total_spots = len(spots)
            if total_spots > 0:
                avg_rating = sum(spot['rating'] for spot in spots) / total_spots
                free_spots = len([spot for spot in spots if spot['price'] == '0'])
                
                print(f"\n=== 统计信息 ===")
                print(f"总景点数: {total_spots}")
                print(f"平均评分: {avg_rating:.2f}")
                print(f"免费景点: {free_spots}个")
                print(f"付费景点: {total_spots - free_spots}个")
        else:
            print("爬取失败，未获取到景点信息")
    except Exception as e:
        logger.error(f"主程序错误: {str(e)}")
    finally:
        # 确保关闭资源
        crawler.close()

# 运行主函数
if __name__ == "__main__":
    main()