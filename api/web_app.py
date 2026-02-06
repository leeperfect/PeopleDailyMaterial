#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web应用模块
"""

import os
import json
import logging
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# 导入模块
from modules.utils import Config, setup_logger
from modules.exporter import DataExporter
from modules.analyzer import HotTopicAnalyzer, PolicyAnalyzer

app = Flask(__name__)


class WebApp:
    """Web应用类"""
    def __init__(self, config: Dict):
        """初始化Web应用"""
        self.config = config
        self.exporter = DataExporter(config.get('export', {}))
        self.hot_topic_analyzer = HotTopicAnalyzer(config.get('analyzer', {}))
        self.policy_analyzer = PolicyAnalyzer(config.get('analyzer', {}))
    
    def get_articles(self, date: Optional[str] = None) -> List[Dict]:
        """获取文章"""
        try:
            # 从本地文件加载文章数据
            if date:
                file_path = f"data/processed/articles_{date.replace('-', '')}.json"
            else:
                # 加载最新的文章数据
                files = sorted([f for f in os.listdir('data/processed') if f.startswith('articles_') and f.endswith('.json')], reverse=True)
                if not files:
                    return []
                file_path = os.path.join('data/processed', files[0])
            
            if not os.path.exists(file_path):
                return []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                articles = json.load(f)
            
            return articles
        except Exception as e:
            logging.error(f"获取文章失败: {str(e)}")
            return []
    
    def get_hot_topics(self, days: int = 7) -> List[Dict]:
        """获取热点话题"""
        try:
            # 从本地文件加载热点话题数据
            files = sorted([f for f in os.listdir('data/processed') if f.startswith('hot_topics_') and f.endswith('.json')], reverse=True)
            if not files:
                # 如果没有热点话题数据，尝试生成
                articles = self.get_articles()
                if not articles:
                    return []
                return self.hot_topic_analyzer.predict_hot_topics(articles, days=days)
            
            file_path = os.path.join('data/processed', files[0])
            with open(file_path, 'r', encoding='utf-8') as f:
                hot_topics = json.load(f)
            
            return hot_topics
        except Exception as e:
            logging.error(f"获取热点话题失败: {str(e)}")
            return []
    
    def get_policy_trends(self) -> List[Dict]:
        """获取政策趋势"""
        try:
            # 从本地文件加载政策趋势数据
            files = sorted([f for f in os.listdir('data/processed') if f.startswith('policy_trends_') and f.endswith('.json')], reverse=True)
            if not files:
                # 如果没有政策趋势数据，尝试生成
                articles = self.get_articles()
                if not articles:
                    return []
                return self.policy_analyzer.analyze_policy_trends(articles)
            
            file_path = os.path.join('data/processed', files[0])
            with open(file_path, 'r', encoding='utf-8') as f:
                policy_trends = json.load(f)
            
            return policy_trends
        except Exception as e:
            logging.error(f"获取政策趋势失败: {str(e)}")
            return []
    
    def get_article_clusters(self) -> List[Dict]:
        """获取文章聚类"""
        try:
            # 从本地文件加载文章聚类数据
            files = sorted([f for f in os.listdir('data/processed') if f.startswith('article_clusters_') and f.endswith('.json')], reverse=True)
            if not files:
                return []
            
            file_path = os.path.join('data/processed', files[0])
            with open(file_path, 'r', encoding='utf-8') as f:
                clusters = json.load(f)
            
            return clusters
        except Exception as e:
            logging.error(f"获取文章聚类失败: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        try:
            articles = self.get_articles()
            hot_topics = self.get_hot_topics()
            policy_trends = self.get_policy_trends()
            clusters = self.get_article_clusters()
            
            # 计算统计信息
            stats = {
                'total_articles': len(articles),
                'total_hot_topics': len(hot_topics),
                'total_policy_trends': len(policy_trends),
                'total_clusters': len(clusters),
                'categories': {},
                'plates': {}
            }
            
            # 统计分类
            for article in articles:
                category = article.get('category', '其他')
                stats['categories'][category] = stats['categories'].get(category, 0) + 1
                
                plate = article.get('plate', '其他')
                stats['plates'][plate] = stats['plates'].get(plate, 0) + 1
            
            return stats
        except Exception as e:
            logging.error(f"获取统计信息失败: {str(e)}")
            return {}


# 全局配置和应用实例
config = {}
web_app = None


def init_app(app_config: Dict):
    """初始化应用"""
    global config, web_app
    config = app_config
    web_app = WebApp(config)


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/api/statistics')
def api_statistics():
    """获取统计信息API"""
    try:
        stats = web_app.get_statistics()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logging.error(f"获取统计信息失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/hot-topics')
def api_hot_topics():
    """获取热点话题API"""
    try:
        days = int(request.args.get('days', 7))
        hot_topics = web_app.get_hot_topics(days=days)
        return jsonify({
            'success': True,
            'data': hot_topics
        })
    except Exception as e:
        logging.error(f"获取热点话题失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/policy-trends')
def api_policy_trends():
    """获取政策趋势API"""
    try:
        policy_trends = web_app.get_policy_trends()
        return jsonify({
            'success': True,
            'data': policy_trends
        })
    except Exception as e:
        logging.error(f"获取政策趋势失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/article-clusters')
def api_article_clusters():
    """获取文章聚类API"""
    try:
        clusters = web_app.get_article_clusters()
        return jsonify({
            'success': True,
            'data': clusters
        })
    except Exception as e:
        logging.error(f"获取文章聚类失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/articles')
def api_articles():
    """获取文章API"""
    try:
        date = request.args.get('date')
        articles = web_app.get_articles(date=date)
        return jsonify({
            'success': True,
            'data': articles
        })
    except Exception as e:
        logging.error(f"获取文章失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# 创建模板目录和静态文件目录
os.makedirs('api/templates', exist_ok=True)
os.makedirs('api/static/css', exist_ok=True)
os.makedirs('api/static/js', exist_ok=True)


# 创建首页模板
index_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>人民日报素材系统</title>
    <!-- Bootstrap CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js"></script>
    <style>
        body {
            font-family: 'Microsoft YaHei', Arial, sans-serif;
            background-color: #f8f9fa;
        }
        .dashboard-card {
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        .dashboard-card .card-header {
            background-color: #007bff;
            color: white;
            border-radius: 10px 10px 0 0;
        }
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 20px;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        .stat-value {
            font-size: 2rem;
            font-weight: bold;
            color: #007bff;
        }
        .stat-label {
            font-size: 1rem;
            color: #6c757d;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <div class="container mt-4">
        <h1 class="text-center mb-4">人民日报素材系统</h1>
        
        <!-- 统计信息 -->
        <div class="stats-grid" id="stats-grid">
            <div class="stat-card">
                <div class="stat-value" id="total-articles">0</div>
                <div class="stat-label">总文章数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="total-hot-topics">0</div>
                <div class="stat-label">热点话题数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="total-policy-trends">0</div>
                <div class="stat-label">政策趋势数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="total-clusters">0</div>
                <div class="stat-label">主题聚类数</div>
            </div>
        </div>
        
        <!-- 热点话题 -->
        <div class="card dashboard-card">
            <div class="card-header">
                <h2 class="card-title">热点话题分析</h2>
            </div>
            <div class="card-body">
                <div class="chart-container">
                    <canvas id="hot-topics-chart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- 文章分类 -->
        <div class="card dashboard-card">
            <div class="card-header">
                <h2 class="card-title">文章分类统计</h2>
            </div>
            <div class="card-body">
                <div class="chart-container">
                    <canvas id="categories-chart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- 政策趋势 -->
        <div class="card dashboard-card">
            <div class="card-header">
                <h2 class="card-title">政策趋势分析</h2>
            </div>
            <div class="card-body">
                <div class="chart-container">
                    <canvas id="policy-trends-chart"></canvas>
                </div>
            </div>
        </div>
        
        <!-- 最新文章 -->
        <div class="card dashboard-card">
            <div class="card-header">
                <h2 class="card-title">最新文章</h2>
            </div>
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>标题</th>
                                <th>分类</th>
                                <th>版面</th>
                                <th>日期</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="articles-table">
                            <tr>
                                <td colspan="5" class="text-center">加载中...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // 加载统计信息
        fetch('/api/statistics')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('total-articles').textContent = data.data.total_articles;
                    document.getElementById('total-hot-topics').textContent = data.data.total_hot_topics;
                    document.getElementById('total-policy-trends').textContent = data.data.total_policy_trends;
                    document.getElementById('total-clusters').textContent = data.data.total_clusters;
                    
                    // 文章分类图表
                    const categoriesCtx = document.getElementById('categories-chart').getContext('2d');
                    new Chart(categoriesCtx, {
                        type: 'pie',
                        data: {
                            labels: Object.keys(data.data.categories),
                            datasets: [{
                                data: Object.values(data.data.categories),
                                backgroundColor: [
                                    '#007bff', '#28a745', '#ffc107', '#dc3545',
                                    '#6f42c1', '#17a2b8', '#fd7e14', '#20c997'
                                ]
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false
                        }
                    });
                }
            });
        
        // 加载热点话题
        fetch('/api/hot-topics')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const topics = data.data.slice(0, 10);
                    const labels = topics.map(topic => topic.keyword);
                    const scores = topics.map(topic => topic.score);
                    
                    const hotTopicsCtx = document.getElementById('hot-topics-chart').getContext('2d');
                    new Chart(hotTopicsCtx, {
                        type: 'bar',
                        data: {
                            labels: labels,
                            datasets: [{
                                label: '热度评分',
                                data: scores,
                                backgroundColor: '#007bff'
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            scales: {
                                y: {
                                    beginAtZero: true
                                }
                            }
                        }
                    });
                }
            });
        
        // 加载政策趋势
        fetch('/api/policy-trends')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const trends = data.data.slice(0, 10).reverse();
                    const dates = trends.map(trend => trend.date);
                    const counts = trends.map(trend => trend.policy_count);
                    
                    const policyTrendsCtx = document.getElementById('policy-trends-chart').getContext('2d');
                    new Chart(policyTrendsCtx, {
                        type: 'line',
                        data: {
                            labels: dates,
                            datasets: [{
                                label: '政策数量',
                                data: counts,
                                borderColor: '#28a745',
                                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                                tension: 0.1
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false
                        }
                    });
                }
            });
        
        // 加载最新文章
        fetch('/api/articles')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const articles = data.data.slice(0, 10);
                    const tableBody = document.getElementById('articles-table');
                    tableBody.innerHTML = '';
                    
                    articles.forEach(article => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${article.title}</td>
                            <td>${article.category}</td>
                            <td>${article.plate}</td>
                            <td>${article.date}</td>
                            <td><a href="${article.url}" target="_blank" class="btn btn-sm btn-primary">查看原文</a></td>
                        `;
                        tableBody.appendChild(row);
                    });
                }
            });
    </script>
</body>
</html>
'''

# 写入首页模板
with open('api/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(index_template)


if __name__ == '__main__':
    # 默认配置
    default_config = {
        'export': {
            'dir': 'data/exports'
        },
        'api': {
            'host': '0.0.0.0',
            'port': 5000,
            'debug': True
        }
    }
    
    init_app(default_config)
    app.run(
        host=default_config['api']['host'],
        port=default_config['api']['port'],
        debug=default_config['api']['debug']
    )
