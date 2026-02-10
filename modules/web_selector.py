#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web UI 文章选择器 - 本地浏览器界面，鼠标点选文章
"""

import json
import logging
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
from typing import List, Dict, Optional, Set


class ArticleSelector:
    """通过本地 Web 页面让用户点选文章"""
    
    def __init__(self, date_str: str, articles_by_section: List[Dict]):
        """
        date_str: 日期字符串，如 "2026-02-10"
        articles_by_section: [
            {
                'section_id': '01',
                'articles': [
                    {'index': 1, 'title': '...', 'auto_skip': False, ...},
                ]
            },
        ]
        """
        self.date_str = date_str
        self.articles_by_section = articles_by_section
        self.selected_indices: Set[int] = set()
        self.selection_done = threading.Event()
        self.server = None
    
    def show_and_wait(self) -> Set[int]:
        """启动 Web 界面并等待用户选择，返回选中的文章编号"""
        port = 18765
        handler = self._make_handler()
        self.server = HTTPServer(('127.0.0.1', port), handler)
        
        # 后台启动服务器
        server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        server_thread.start()
        
        url = f'http://127.0.0.1:{port}'
        print(f"\n  🌐 已打开文章选择页面: {url}")
        print(f"  📝 请在浏览器中勾选要下载的文章，然后点击「开始下载」按钮")
        print(f"  ⏳ 等待你的选择...\n")
        
        webbrowser.open(url)
        
        # 等待用户提交选择
        self.selection_done.wait()
        self.server.shutdown()
        
        return self.selected_indices
    
    def _make_handler(self):
        selector = self
        
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # 静默日志
            
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                html = selector._generate_html()
                self.wfile.write(html.encode('utf-8'))
            
            def do_POST(self):
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8')
                
                try:
                    data = json.loads(body)
                    selector.selected_indices = set(data.get('selected', []))
                except Exception:
                    selector.selected_indices = set()
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': True}).encode('utf-8'))
                
                # 通知主线程选择完成
                selector.selection_done.set()
        
        return Handler
    
    def _generate_html(self) -> str:
        """生成文章选择页面 HTML"""
        sections_html = ""
        
        for section in self.articles_by_section:
            section_id = section['section_id']
            section_name = section.get('section_name', '')
            articles = section['articles']
            
            if not articles:
                continue
            
            items_html = ""
            for art in articles:
                idx = art['index']
                title = art['title']
                auto_skip = art.get('auto_skip', False)
                
                if auto_skip:
                    items_html += f'''
                    <label class="article-item skipped">
                        <input type="checkbox" value="{idx}" disabled>
                        <span class="idx">{idx}</span>
                        <span class="title">{title}</span>
                        <span class="badge skip">已过滤</span>
                    </label>'''
                else:
                    items_html += f'''
                    <label class="article-item">
                        <input type="checkbox" value="{idx}" class="article-cb">
                        <span class="idx">{idx}</span>
                        <span class="title">{title}</span>
                    </label>'''
            
            # 显示版面号 + 版面名称
            section_label = f'第 {section_id} 版 · {section_name}' if section_name else f'第 {section_id} 版'
            
            sections_html += f'''
            <div class="section">
                <div class="section-header">
                    <label class="section-select-all">
                        <input type="checkbox" class="section-all-cb">
                        <span>{section_label}</span>
                    </label>
                    <span class="section-count">{len([a for a in articles if not a.get('auto_skip')])} 篇</span>
                </div>
                <div class="section-body">{items_html}</div>
            </div>'''
        
        total = sum(len(s['articles']) for s in self.articles_by_section)
        available = sum(1 for s in self.articles_by_section for a in s['articles'] if not a.get('auto_skip'))
        
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>人民日报 {self.date_str} - 文章选择</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');
  
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  
  body {{
    font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
    color: #e0e0e0;
  }}
  
  .container {{
    max-width: 900px;
    margin: 0 auto;
    padding: 30px 20px 120px;
  }}
  
  .header {{
    text-align: center;
    margin-bottom: 30px;
  }}
  
  .header h1 {{
    font-size: 28px;
    font-weight: 700;
    background: linear-gradient(90deg, #f7971e, #ffd200);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
  }}
  
  .header .subtitle {{
    color: #888;
    font-size: 14px;
  }}
  
  .toolbar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding: 12px 18px;
    background: rgba(255,255,255,0.05);
    border-radius: 12px;
    backdrop-filter: blur(10px);
  }}
  
  .toolbar .left {{
    display: flex;
    gap: 12px;
    align-items: center;
  }}
  
  .toolbar button {{
    padding: 6px 16px;
    border: 1px solid rgba(255,255,255,0.15);
    background: rgba(255,255,255,0.08);
    color: #ccc;
    border-radius: 8px;
    cursor: pointer;
    font-size: 13px;
    transition: all 0.2s;
  }}
  
  .toolbar button:hover {{
    background: rgba(255,255,255,0.15);
    color: #fff;
  }}
  
  .selected-count {{
    font-size: 14px;
    color: #ffd200;
    font-weight: 500;
  }}
  
  .section {{
    margin-bottom: 16px;
    background: rgba(255,255,255,0.04);
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,0.06);
  }}
  
  .section-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 18px;
    background: rgba(255,255,255,0.06);
    cursor: pointer;
  }}
  
  .section-header label {{
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 500;
    font-size: 15px;
    color: #fff;
  }}
  
  .section-count {{
    font-size: 12px;
    color: #888;
  }}
  
  .section-body {{
    padding: 4px 0;
  }}
  
  .article-item {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 18px;
    cursor: pointer;
    transition: background 0.15s;
    border-bottom: 1px solid rgba(255,255,255,0.03);
  }}
  
  .article-item:hover {{
    background: rgba(255,255,255,0.06);
  }}
  
  .article-item.skipped {{
    opacity: 0.35;
    cursor: not-allowed;
  }}
  
  .article-item.selected {{
    background: rgba(247, 151, 30, 0.1);
    border-left: 3px solid #f7971e;
  }}
  
  .article-item input[type="checkbox"] {{
    width: 18px;
    height: 18px;
    accent-color: #f7971e;
    cursor: pointer;
    flex-shrink: 0;
  }}
  
  .section-header input[type="checkbox"] {{
    width: 16px;
    height: 16px;
    accent-color: #ffd200;
    cursor: pointer;
  }}
  
  .article-item .idx {{
    font-size: 12px;
    color: #666;
    min-width: 28px;
    text-align: right;
    flex-shrink: 0;
  }}
  
  .article-item .title {{
    flex: 1;
    font-size: 14px;
    line-height: 1.5;
  }}
  
  .badge {{
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 4px;
    flex-shrink: 0;
  }}
  
  .badge.skip {{
    background: rgba(255,255,255,0.08);
    color: #666;
  }}
  
  /* 底部固定操作栏 */
  .bottom-bar {{
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 16px 20px;
    background: rgba(15, 12, 41, 0.95);
    backdrop-filter: blur(20px);
    border-top: 1px solid rgba(255,255,255,0.1);
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
    z-index: 100;
  }}
  
  .btn-download {{
    padding: 12px 40px;
    background: linear-gradient(90deg, #f7971e, #ffd200);
    color: #1a1a2e;
    border: none;
    border-radius: 10px;
    font-size: 16px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s;
    box-shadow: 0 4px 15px rgba(247, 151, 30, 0.3);
  }}
  
  .btn-download:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 25px rgba(247, 151, 30, 0.5);
  }}
  
  .btn-download:disabled {{
    opacity: 0.4;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }}
  
  .done-overlay {{
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(15, 12, 41, 0.9);
    z-index: 200;
    justify-content: center;
    align-items: center;
    flex-direction: column;
    gap: 16px;
  }}
  
  .done-overlay.show {{
    display: flex;
  }}
  
  .done-overlay .icon {{
    font-size: 64px;
  }}
  
  .done-overlay .text {{
    font-size: 20px;
    color: #ffd200;
    font-weight: 500;
  }}

  .done-overlay .subtext {{
    color: #888;
    font-size: 14px;
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>📰 人民日报 {self.date_str}</h1>
    <div class="subtitle">共 {total} 篇文章，{available} 篇可选择下载</div>
  </div>
  
  <div class="toolbar">
    <div class="left">
      <button onclick="selectAll()">全选</button>
      <button onclick="deselectAll()">全不选</button>
      <button onclick="invertAll()">反选</button>
    </div>
    <div class="selected-count">已选 <span id="count">0</span> 篇</div>
  </div>
  
  {sections_html}
</div>

<div class="bottom-bar">
  <span class="selected-count">已选 <span id="count2">0</span> 篇文章</span>
  <button class="btn-download" id="btnDownload" onclick="submitSelection()" disabled>开始下载</button>
</div>

<div class="done-overlay" id="doneOverlay">
  <div class="icon">✅</div>
  <div class="text">选择已提交！</div>
  <div class="subtext">请回到终端查看下载进度，此页面可以关闭</div>
</div>

<script>
function updateCount() {{
  const checked = document.querySelectorAll('.article-cb:checked');
  const n = checked.length;
  document.getElementById('count').textContent = n;
  document.getElementById('count2').textContent = n;
  document.getElementById('btnDownload').disabled = n === 0;
  
  // 更新选中样式
  document.querySelectorAll('.article-item:not(.skipped)').forEach(el => {{
    const cb = el.querySelector('.article-cb');
    if (cb) el.classList.toggle('selected', cb.checked);
  }});
  
  // 更新版面全选状态
  document.querySelectorAll('.section').forEach(sec => {{
    const allCb = sec.querySelector('.section-all-cb');
    const cbs = sec.querySelectorAll('.article-cb');
    const checkedCbs = sec.querySelectorAll('.article-cb:checked');
    if (cbs.length > 0) {{
      allCb.checked = checkedCbs.length === cbs.length;
      allCb.indeterminate = checkedCbs.length > 0 && checkedCbs.length < cbs.length;
    }}
  }});
}}

// 版面全选
document.querySelectorAll('.section-all-cb').forEach(allCb => {{
  allCb.addEventListener('change', function() {{
    const section = this.closest('.section');
    section.querySelectorAll('.article-cb').forEach(cb => {{
      cb.checked = allCb.checked;
    }});
    updateCount();
  }});
}});

// 单个文章勾选
document.querySelectorAll('.article-cb').forEach(cb => {{
  cb.addEventListener('change', updateCount);
}});

function selectAll() {{
  document.querySelectorAll('.article-cb').forEach(cb => cb.checked = true);
  updateCount();
}}

function deselectAll() {{
  document.querySelectorAll('.article-cb').forEach(cb => cb.checked = false);
  updateCount();
}}

function invertAll() {{
  document.querySelectorAll('.article-cb').forEach(cb => cb.checked = !cb.checked);
  updateCount();
}}

function submitSelection() {{
  const selected = [];
  document.querySelectorAll('.article-cb:checked').forEach(cb => {{
    selected.push(parseInt(cb.value));
  }});
  
  fetch('/', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ selected: selected }})
  }}).then(() => {{
    document.getElementById('doneOverlay').classList.add('show');
  }});
}}
</script>
</body>
</html>'''
