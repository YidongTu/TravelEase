// 全局变量
const API_BASE_URL = 'http://localhost:5000/api';
let currentUser = null;

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 检查用户是否已登录
    checkUserLoggedIn();
    
    // 绑定表单提交事件
    if (document.getElementById('loginForm')) {
        document.getElementById('loginForm').addEventListener('submit', handleLogin);
    }
    
    if (document.getElementById('registerForm')) {
        document.getElementById('registerForm').addEventListener('submit', handleRegister);
    }
    
    if (document.getElementById('assessmentForm')) {
        document.getElementById('assessmentForm').addEventListener('submit', handleAssessment);
    }
    
    if (document.getElementById('cityForm')) {
        document.getElementById('cityForm').addEventListener('submit', handleCitySelection);
    }
    
    if (document.getElementById('rankingFilterForm')) {
        document.getElementById('rankingFilterForm').addEventListener('submit', handleRankingFilter);
    }
    
    if (document.getElementById('recommendationsFilterForm')) {
        document.getElementById('recommendationsFilterForm').addEventListener('submit', handleRecommendationsFilter);
    }
    
    // 绑定退出登录事件
    if (document.getElementById('logout')) {
        document.getElementById('logout').addEventListener('click', handleLogout);
    }
    
    // 如果是景点详情页，加载景点详情
    if (window.location.pathname.includes('attraction_details.html')) {
        const params = new URLSearchParams(window.location.search);
        const attractionId = params.get('id');
        if (attractionId) {
            loadAttractionDetails(attractionId);
        }
    }
    
    // 如果是推荐页面，加载推荐景点
    if (window.location.pathname.includes('recommendations.html')) {
        loadRecommendations();
    }
});

// 检查用户是否已登录
function checkUserLoggedIn() {
    const token = localStorage.getItem('token');
    const isAuthPage = window.location.pathname.includes('index.html') || 
                      window.location.pathname.includes('register.html');
    
    if (token) {
        // 验证token并获取用户信息
        fetch(`${API_BASE_URL}/auth/verify`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Token验证失败');
            }
        })
        .then(data => {
            currentUser = data.user;
            
            // 如果在登录/注册页面且已登录，跳转到兴趣评估页面
            if (isAuthPage) {
                window.location.href = 'interest_assessment.html';
            } else {
                // 检查用户是否已完成兴趣评估
                if (window.location.pathname.includes('interest_assessment.html') && 
                    currentUser.has_completed_assessment) {
                    // 如果已完成评估，跳转到城市景点页面
                    window.location.href = 'city_attractions.html';
                } else if (!window.location.pathname.includes('interest_assessment.html') && 
                           !currentUser.has_completed_assessment) {
                    // 如果未完成评估且不在评估页面，跳转到评估页面
                    window.location.href = 'interest_assessment.html';
                }
                
                // 在推荐页面检查是否已完成评估
                if (window.location.pathname.includes('recommendations.html') && 
                    !currentUser.has_completed_assessment) {
                    document.getElementById('noAssessmentMessage').style.display = 'block';
                }
            }
        })
        .catch(error => {
            console.error('登录状态验证失败:', error);
            localStorage.removeItem('token');
            currentUser = null;
            
            // 如果不在登录/注册页面且未登录，跳转到登录页面
            if (!isAuthPage) {
                window.location.href = 'index.html';
            }
        });
    } else {
        // 如果不在登录/注册页面且未登录，跳转到登录页面
        if (!isAuthPage) {
            window.location.href = 'index.html';
        }
    }
}

// 处理登录
function handleLogin(e) {
    e.preventDefault();
    
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    
    fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            return response.json().then(data => {
                throw new Error(data.message || '登录失败');
            });
        }
    })
    .then(data => {
        localStorage.setItem('token', data.token);
        // 登录成功后跳转到兴趣评估页面
        window.location.href = 'interest_assessment.html';
    })
    .catch(error => {
        alert(error.message);
    });
}

// 处理注册
function handleRegister(e) {
    e.preventDefault();
    
    const name = document.getElementById('register-name').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm').value;
    
    if (password !== confirmPassword) {
        alert('两次输入的密码不一致');
        return;
    }
    
    fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name, email, password })
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            return response.json().then(data => {
                throw new Error(data.message || '注册失败');
            });
        }
    })
    .then(data => {
        alert('注册成功，请登录');
        window.location.href = 'index.html';
    })
    .catch(error => {
        alert(error.message);
    });
}

// 处理退出登录
function handleLogout(e) {
    e.preventDefault();
    localStorage.removeItem('token');
    window.location.href = 'index.html';
}

// 处理兴趣评估提交
function handleAssessment(e) {
    e.preventDefault();
    
    // 收集表单数据
    const formData = {
        q1: document.querySelector('input[name="q1"]:checked').value,
        q2: document.querySelector('input[name="q2"]:checked').value,
        q3: document.querySelector('input[name="q3"]:checked').value,
        q4: Array.from(document.querySelectorAll('input[name="q4"]:checked')).map(checkbox => checkbox.value),
        q5: document.querySelector('input[name="q5"]:checked').value,
        q6: document.querySelector('input[name="q6"]:checked').value,
        q7: Array.from(document.querySelectorAll('input[name="q7"]:checked')).map(checkbox => checkbox.value)
    };
    
    const token = localStorage.getItem('token');
    
    fetch(`${API_BASE_URL}/assessment`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('提交评估失败');
        }
    })
    .then(data => {
        alert('兴趣评估已完成，正在为您推荐景点...');
        window.location.href = 'city_attractions.html';
    })
    .catch(error => {
        alert(error.message);
    });
}

// 处理城市选择
function handleCitySelection(e) {
    e.preventDefault();
    
    const city = document.getElementById('city').value;
    const token = localStorage.getItem('token');
    
    // 显示加载指示器
    document.getElementById('loadingIndicator').style.display = 'block';
    document.getElementById('attractionsContainer').innerHTML = '';
    
    fetch(`${API_BASE_URL}/attractions?city=${encodeURIComponent(city)}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('获取景点数据失败');
        }
    })
    .then(data => {
        // 隐藏加载指示器
        document.getElementById('loadingIndicator').style.display = 'none';
        
        // 显示景点列表
        const container = document.getElementById('attractionsContainer');
        if (data.attractions.length === 0) {
            container.innerHTML = '<p>未找到该城市的景点数据</p>';
            return;
        }
        
        data.attractions.forEach(attraction => {
            const card = createAttractionCard(attraction);
            container.appendChild(card);
        });
    })
    .catch(error => {
        document.getElementById('loadingIndicator').style.display = 'none';
        alert(error.message);
    });
}

// 创建景点卡片
function createAttractionCard(attraction) {
    const card = document.createElement('div');
    card.className = 'attraction-card';
    card.addEventListener('click', () => {
        window.location.href = `attraction_details.html?id=${attraction.id}`;
    });
    
    card.innerHTML = `
        <div class="attraction-image">
            <img src="${attraction.images[0] || 'https://picsum.photos/400/300'}" alt="${attraction.name}">
        </div>
        <div class="attraction-card-content">
            <h3>${attraction.name}</h3>
            <div class="score"><i class="fas fa-star"></i> 综合评分: ${attraction.overall_score.toFixed(1)}</div>
            ${attraction.match_score ? `<div class="match"><i class="fas fa-heart"></i> 与您的匹配度: ${Math.round(attraction.match_score * 100)}%</div>` : ''}
            <p>${attraction.description.substring(0, 100)}${attraction.description.length > 100 ? '...' : ''}</p>
        </div>
    `;
    
    return card;
}

// 加载景点详情
function loadAttractionDetails(attractionId) {
    const token = localStorage.getItem('token');
    
    fetch(`${API_BASE_URL}/attractions/${attractionId}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('获取景点详情失败');
        }
    })
    .then(data => {
        // 隐藏加载指示器，显示内容
        document.getElementById('loadingIndicator').style.display = 'none';
        document.getElementById('attractionContent').style.display = 'block';
        
        const attraction = data.attraction;
        
        // 填充基本信息
        document.getElementById('attractionName').textContent = attraction.name;
        document.getElementById('attractionLocation').textContent = `${attraction.city} · ${attraction.address || '地址未知'}`;
        document.getElementById('attractionScore').textContent = `评分：${attraction.overall_score.toFixed(1)}`;
        
        // 填充匹配度（如果有）
        if (attraction.match_score) {
            document.getElementById('attractionMatch').textContent = `匹配度：${Math.round(attraction.match_score * 100)}%`;
        }
        
        // 填充图片画廊
        const gallery = document.getElementById('attractionGallery');
        attraction.images.forEach(img => {
            const imgElement = document.createElement('img');
            imgElement.src = img;
            imgElement.alt = `${attraction.name}的照片`;
            gallery.appendChild(imgElement);
        });
        
        // 填充描述和基本信息
        document.getElementById('attractionDescription').textContent = attraction.description;
        document.getElementById('attractionHours').textContent = attraction.opening_hours || '信息未提供';
        document.getElementById('attractionPrice').textContent = attraction.ticket_price || '信息未提供';
        document.getElementById('attractionTime').textContent = attraction.recommended_time || '信息未提供';
        document.getElementById('attractionType').textContent = attraction.type || '信息未提供';
        
        // 填充评估图表
        const scores = attraction.assessment_scores;
        document.getElementById('sceneryScore').style.width = `${scores.scenery * 10}%`;
        document.getElementById('sceneryValue').textContent = scores.scenery;
        
        document.getElementById('cultureScore').style.width = `${scores.culture * 10}%`;
        document.getElementById('cultureValue').textContent = scores.culture;
        
        document.getElementById('facilityScore').style.width = `${scores.facility * 10}%`;
        document.getElementById('facilityValue').textContent = scores.facility;
        
        document.getElementById('serviceScore').style.width = `${scores.service * 10}%`;
        document.getElementById('serviceValue').textContent = scores.service;
        
        document.getElementById('valueScore').style.width = `${scores.value * 10}%`;
        document.getElementById('valueValue').textContent = scores.value;
        
        // 填充评估总结
        document.getElementById('assessmentSummary').textContent = attraction.assessment_summary || '暂无评估总结';
        
        // 填充游客评价
        const reviewsContainer = document.getElementById('reviewsContainer');
        if (attraction.reviews && attraction.reviews.length > 0) {
            attraction.reviews.forEach(review => {
                const reviewElement = document.createElement('div');
                reviewElement.className = 'review-item';
                reviewElement.innerHTML = `
                    <div class="review-header">
                        <span class="review-author">${review.author || '匿名用户'}</span>
                        <span class="review-rating"><i class="fas fa-star"></i> ${review.rating}</span>
                    </div>
                    <p>${review.content}</p>
                `;
                reviewsContainer.appendChild(reviewElement);
            });
        } else {
            reviewsContainer.innerHTML = '<p>暂无游客评价</p>';
        }
    })
    .catch(error => {
        document.getElementById('loadingIndicator').textContent = '加载失败，请重试';
        console.error(error);
    });
}

// 处理排行榜筛选
function handleRankingFilter(e) {
    e.preventDefault();
    
    const city = document.getElementById('rankingCity').value;
    const rankingType = document.getElementById('rankingType').value;
    const token = localStorage.getItem('token');
    
    // 显示加载指示器
    document.getElementById('loadingIndicator').style.display = 'block';
    document.getElementById('rankingContainer').innerHTML = '';
    
    fetch(`${API_BASE_URL}/rankings?city=${encodeURIComponent(city)}&type=${encodeURIComponent(rankingType)}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            throw new Error('获取排行榜数据失败');
        }
    })
    .then(data => {
        // 隐藏加载指示器
        document.getElementById('loadingIndicator').style.display = 'none';
        
        // 显示排行榜
        const container = document.getElementById('rankingContainer');
        if (data.rankings.length === 0) {
            container.innerHTML = '<p>未找到该城市的景点排名数据</p>';
            return;
        }
        
        data.rankings.forEach((attraction, index) => {
            const rankingItem = document.createElement('div');
            rankingItem.className = 'ranking-item';
            rankingItem.addEventListener('click', () => {
                window.location.href = `attraction_details.html?id=${attraction.id}`;
            });
            
            rankingItem.innerHTML = `
                <div class="ranking-position">${index + 1}</div>
                <div class="ranking-image">
                    <img src="${attraction.images[0] || 'https://picsum.photos/300/200'}" alt="${attraction.name}">
                </div>
                <div class="ranking-content">
                    <h3>${attraction.name}</h3>
                    <div class="ranking-meta">
                        <span>${attraction.city}</span>
                        <span>${attraction.type || '未知类型'}</span>
                    </div>
                    <div class="ranking-score"><i class="fas fa-star"></i> ${rankingType}: ${attraction.assessment_scores[rankingType === '综合评分' ? 'overall' : 
                                                                                           rankingType === '风景指数' ? 'scenery' :
                                                                                           rankingType === '文化体验' ? 'culture' :
                                                                                           rankingType === '娱乐设施' ? 'facility' :
                                                                                           rankingType === '服务质量' ? 'service' : 'value']}</div>
                    <p>${attraction.description.substring(0, 150)}${attraction.description.length > 150 ? '...' : ''}</p>
                </div>
            `;
            
            container.appendChild(rankingItem);
        });
    })
    .catch(error => {
        document.getElementById('loadingIndicator').style.display = 'none';
        alert(error.message);
    });
}

// 加载推荐景点
function loadRecommendations(city = '') {
    const token = localStorage.getItem('token');
    
    // 显示加载指示器
    document.getElementById('loadingIndicator').style.display = 'block';
    document.getElementById('recommendationsContainer').innerHTML = '';
    
    let url = `${API_BASE_URL}/recommendations`;
    if (city) {
        url += `?city=${encodeURIComponent(city)}`;
    }
    
    fetch(url, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (response.ok) {
            return response.json();
        } else {
            return response.json().then(data => {
                throw new Error(data.message || '获取推荐景点失败');
            });
        }
    })
    .then(data => {
        // 隐藏加载指示器
        document.getElementById('loadingIndicator').style.display = 'none';
        
        // 显示推荐景点
        const container = document.getElementById('recommendationsContainer');
        if (data.recommendations.length === 0) {
            container.innerHTML = '<p>暂无为您推荐的景点，请尝试选择其他城市或完成兴趣评估</p>';
            return;
        }
        
        data.recommendations.forEach(attraction => {
            const card = createAttractionCard(attraction);
            container.appendChild(card);
        });
    })
    .catch(error => {
        document.getElementById('loadingIndicator').style.display = 'none';
        alert(error.message);
    });
}

// 处理推荐筛选
function handleRecommendationsFilter(e) {
    e.preventDefault();
    const city = document.getElementById('recommendationCity').value;
    loadRecommendations(city);
}
