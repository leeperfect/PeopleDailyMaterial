#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试系列名称提取功能
"""

import sys
import os
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.parser import ContentParser

# 测试示例网页
TEST_URL = "https://paper.people.com.cn/rmrb/pc/content/202601/29/content_30136561.html"

def test_series_extraction():
    """测试系列名称提取功能"""
    print(f"测试URL: {TEST_URL}")
    print("=" * 80)
    
    # 获取网页内容
    try:
        response = requests.get(TEST_URL, timeout=10)
        response.encoding = 'utf-8'
        html = response.text
    except Exception as e:
        print(f"获取网页失败: {str(e)}")
        return
    
    # 解析文章
    parser = ContentParser()
    article_data = parser.parse_article(html, TEST_URL)
    
    if article_data:
        print(f"提取的标题: {article_data['title']}")
        print(f"提取的系列名称: {article_data['series_name']}")
        print(f"提取的作者: {article_data['author']}")
        print(f"提取的版面: {article_data['plate']}")
        print("\nMarkdown 正文预览:")
        print(article_data['markdown_body'][:500] + "...")
        print("\n" + "=" * 80)
        
        # 验证系列名称是否正确
        expected_series = "透过数据看潜能"
        if expected_series in article_data['series_name']:
            print("✓ 系列名称提取正确！")
            print(f"正确识别系列名称: {article_data['series_name']}")
        else:
            print("✗ 系列名称提取错误！")
            print(f"期望系列名称包含: {expected_series}")
            print(f"实际提取系列名称: {article_data['series_name']}")
    else:
        print("解析文章失败")

if __name__ == "__main__":
    test_series_extraction()
