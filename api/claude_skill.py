#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Claude Skill接口模块
"""

import logging
from flask import Flask, request, jsonify
from typing import List, Dict, Optional
from modules.exporter import DataExporter
from modules.analyzer import HotTopicAnalyzer, PolicyAnalyzer

app = Flask(__name__)


class ClaudeSkillAPI:
    """Claude Skill API类"""
    def __init__(self, config: Dict):
        self.config = config
        self.exporter = DataExporter(config)
        self.hot_topic_analyzer = HotTopicAnalyzer(config)
        self.policy_analyzer = PolicyAnalyzer(config)
    
    def get_articles(self, date: Optional[str] = None, category: Optional[str] = None) -> List[Dict]:
        """获取文章"""
        try:
            # 这里应该从存储中获取文章，暂时返回空列表
            # 实际实现时应该连接到数据库或文件系统
            return []
        except Exception as e:
            logging.error(f"获取文章失败: {str(e)}")
            return []
    
    def get_hot_topics(self, days: int = 7) -> List[Dict]:
        """获取热点话题"""
        try:
            articles = self.get_articles()
            if not articles:
                return []
            
            hot_topics = self.hot_topic_analyzer.predict_hot_topics(articles, days=days)
            return hot_topics
        except Exception as e:
            logging.error(f"获取热点话题失败: {str(e)}")
            return []
    
    def get_policy_trends(self) -> List[Dict]:
        """获取政策趋势"""
        try:
            articles = self.get_articles()
            if not articles:
                return []
            
            policy_trends = self.policy_analyzer.analyze_policy_trends(articles)
            return policy_trends
        except Exception as e:
            logging.error(f"获取政策趋势失败: {str(e)}")
            return []
    
    def analyze_policy(self, article_id: str) -> Dict:
        """分析政策"""
        try:
            # 这里应该根据article_id获取具体文章
            # 实际实现时应该连接到数据库或文件系统
            article = {}
            if not article:
                return {}
            
            policy_impact = self.policy_analyzer.analyze_policy_impact(article)
            return policy_impact
        except Exception as e:
            logging.error(f"分析政策失败: {str(e)}")
            return {}


# 全局配置和API实例
config = {}
claude_skill_api = None


def init_app(app_config: Dict):
    """初始化应用"""
    global config, claude_skill_api
    config = app_config
    claude_skill_api = ClaudeSkillAPI(config)


@app.route('/api/claude/articles', methods=['GET'])
def api_get_articles():
    """获取文章API"""
    try:
        date = request.args.get('date')
        category = request.args.get('category')
        
        articles = claude_skill_api.get_articles(date=date, category=category)
        return jsonify({
            'success': True,
            'data': articles,
            'total': len(articles)
        })
    except Exception as e:
        logging.error(f"API获取文章失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/claude/hot-topics', methods=['GET'])
def api_get_hot_topics():
    """获取热点话题API"""
    try:
        days = int(request.args.get('days', 7))
        
        hot_topics = claude_skill_api.get_hot_topics(days=days)
        return jsonify({
            'success': True,
            'data': hot_topics,
            'total': len(hot_topics)
        })
    except Exception as e:
        logging.error(f"API获取热点话题失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/claude/policy-trends', methods=['GET'])
def api_get_policy_trends():
    """获取政策趋势API"""
    try:
        policy_trends = claude_skill_api.get_policy_trends()
        return jsonify({
            'success': True,
            'data': policy_trends,
            'total': len(policy_trends)
        })
    except Exception as e:
        logging.error(f"API获取政策趋势失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/claude/analyze-policy', methods=['POST'])
def api_analyze_policy():
    """分析政策API"""
    try:
        data = request.json
        article_id = data.get('article_id')
        
        if not article_id:
            return jsonify({
                'success': False,
                'error': '缺少article_id参数'
            }), 400
        
        policy_impact = claude_skill_api.analyze_policy(article_id)
        return jsonify({
            'success': True,
            'data': policy_impact
        })
    except Exception as e:
        logging.error(f"API分析政策失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # 默认配置
    default_config = {
        'export': {
            'dir': 'data/exports'
        }
    }
    
    init_app(default_config)
    app.run(debug=True, host='0.0.0.0', port=5000)
