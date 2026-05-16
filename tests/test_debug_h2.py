#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试 h2 标签处理
"""

import requests
from bs4 import BeautifulSoup

# 测试示例网页
TEST_URL = "https://paper.people.com.cn/rmrb/pc/content/202601/29/content_30136561.html"

def debug_h2_processing():
    """调试 h2 标签处理"""
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
    
    # 解析HTML
    soup = BeautifulSoup(html, 'lxml')
    article_div = soup.find('div', class_='article')
    
    if not article_div:
        print("未找到 div.article")
        return
    
    print("\n=== 分析 article_div 的直接子元素 ===")
    for i, child in enumerate(article_div.children):
        if not hasattr(child, 'name') or not child.name:
            continue
        
        tag = child.name
        text = child.get_text(strip=True)
        classes = child.get('class', [])
        
        print(f"\n子元素 {i+1}:")
        print(f"  标签: {tag}")
        print(f"  类名: {classes}")
        print(f"  文本: {text[:100]}..." if len(text) > 100 else f"  文本: {text}")
        
        # 检查是否有子元素
        if child.children:
            print("  子元素:")
            for j, grandchild in enumerate(child.children):
                if hasattr(grandchild, 'name') and grandchild.name:
                    print(f"    {j+1}. 标签: {grandchild.name}, 文本: {grandchild.get_text(strip=True)[:50]}..." if len(grandchild.get_text(strip=True)) > 50 else f"    {j+1}. 标签: {grandchild.name}, 文本: {grandchild.get_text(strip=True)}")
    
    print("\n=== 直接查找 h1, h2 标签 ===")
    h1 = article_div.find('h1')
    if h1:
        print(f"h1 标签文本: {h1.get_text(strip=True)}")
    
    h2 = article_div.find('h2')
    if h2:
        print(f"h2 标签文本: {h2.get_text(strip=True)}")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    debug_h2_processing()
