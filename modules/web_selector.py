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
    """通过本地 Web 页面让用户点选文章（支持单日/多日模式）"""
    
    def __init__(self, date_str: str = "", articles_by_section: List[Dict] = None,
                 dates_info: List[Dict] = None):
        """
        单日模式: ArticleSelector("2026-01-02", articles_by_section)
        多日模式: ArticleSelector(dates_info=[{'date_str': '...', 'articles_by_section': [...]}, ...])
        """
        if dates_info:
            self.dates_info = dates_info
            self.is_multi_date = True
            date_strs = [d['date_str'] for d in dates_info]
            self.title = f"{date_strs[0]} ~ {date_strs[-1]}"
        else:
            self.dates_info = [{'date_str': date_str, 'articles_by_section': articles_by_section or []}]
            self.is_multi_date = False
            self.title = date_str
        
        self.selected_indices: Set[int] = set()
        self.manual_groups: List[Dict] = []  # 手动编组信息
        self.selection_done = threading.Event()
        self.server = None
    
    def show_and_wait(self) -> Set[int]:
        """启动 Web 界面并等待用户选择，返回选中的文章编号"""
        port = 18765
        handler = self._make_handler()
        self.server = HTTPServer(('127.0.0.1', port), handler)
        self.server.allow_reuse_address = True
        # 修复端口占用：允许端口复用
        import socket
        self.server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
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
                    selector.manual_groups = data.get('groups', [])
                except Exception:
                    selector.selected_indices = set()
                    selector.manual_groups = []
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': True}).encode('utf-8'))
                
                # 通知主线程选择完成
                selector.selection_done.set()
        
        return Handler
    
    def _generate_html(self) -> str:
        """生成文章选择页面 HTML（支持多日分组 + 系列标签）"""
        content_html = ""
        total_articles = 0
        available_articles = 0
        
        # 收集所有系列信息用于分配颜色
        series_colors = {}
        color_palette = ['#e74c3c', '#3498db', '#2ecc71', '#9b59b6', '#e67e22', '#1abc9c', '#f39c12', '#e84393']
        color_idx = 0
        for date_item in self.dates_info:
            for section in date_item.get('articles_by_section', []):
                for art in section.get('articles', []):
                    sid = art.get('series_id')
                    if sid and sid not in series_colors:
                        series_colors[sid] = color_palette[color_idx % len(color_palette)]
                        color_idx += 1
        
        for date_item in self.dates_info:
            date_str = date_item['date_str']
            articles_by_section = date_item['articles_by_section']
            
            if not articles_by_section:
                continue
            
            sections_html = ""
            for section in articles_by_section:
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
                    
                    total_articles += 1
                    if not auto_skip:
                        available_articles += 1
                    
                    if auto_skip:
                        items_html += f'''
                        <label class="article-item skipped">
                            <input type="checkbox" value="{idx}" disabled>
                            <span class="idx">{idx}</span>
                            <span class="title">{title}</span>
                            <span class="badge skip">已过滤</span>
                        </label>'''
                    else:
                        series_id = art.get('series_id', '')
                        series_name = art.get('series_name', '')
                        series_badge = ''
                        series_attr = ''
                        if series_id and series_name:
                            color = series_colors.get(series_id, '#888')
                            series_badge = f'<span class="badge series" style="background:{color}20;color:{color};border:1px solid {color}40">🔗 {series_name}</span>'
                            series_attr = f' data-series="{series_id}"'
                        items_html += f'''
                        <label class="article-item"{series_attr}>
                            <input type="checkbox" value="{idx}" class="article-cb">
                            <span class="idx">{idx}</span>
                            <span class="title">{title}</span>
                            {series_badge}
                        </label>'''
                
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
            
            content_html += f'''
            <div class="date-group">
                <div class="date-group-header">📅 {date_str}</div>
                {sections_html}
            </div>'''
        
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>人民日报文章选择 - {self.title}</title>
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
    position: sticky;
    top: 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 25px;
    padding: 12px 18px;
    background: rgba(48, 43, 99, 0.95);
    border-radius: 12px;
    backdrop-filter: blur(15px);
    z-index: 90;
    border: 1px solid rgba(255,255,255,0.1);
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
  
  .date-group {{
    margin-bottom: 35px;
  }}
  
  .date-group-header {{
    font-size: 20px;
    font-weight: 700;
    color: #ffd200;
    margin-bottom: 15px;
    padding: 8px 12px;
    border-left: 4px solid #f7971e;
    background: rgba(255,255,255,0.03);
    border-radius: 0 8px 8px 0;
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
  
  .badge.series {{
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 12px;
    white-space: nowrap;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    cursor: pointer;
    transition: all 0.2s;
  }}
  
  .badge.series:hover {{
    filter: brightness(1.3);
    transform: scale(1.05);
  }}
  
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

  /* ====== 编组面板（常驻） ====== */
  .container {{
    margin-right: 320px;
  }}
  
  /* 编组切换按钮：每行文章右侧的 +/− */
  .group-toggle-btn {{
    display: inline-block;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: rgba(155, 89, 182, 0.15);
    border: 2px solid rgba(155, 89, 182, 0.4);
    color: #bb8fce;
    font-size: 18px;
    font-weight: 700;
    line-height: 24px;
    text-align: center;
    cursor: pointer;
    flex-shrink: 0;
    transition: all 0.2s;
    margin-left: auto;
  }}
  .group-toggle-btn:hover {{
    background: rgba(155, 89, 182, 0.35);
    transform: scale(1.15);
  }}
  .group-toggle-btn.added {{
    background: rgba(155, 89, 182, 0.5);
    border-color: #bb8fce;
    color: #fff;
  }}
  
  .article-item.in-group {{
    border-left: 4px solid #9b59b6 !important;
    padding-left: 8px;
    background: rgba(155, 89, 182, 0.08) !important;
  }}
  
  .group-panel {{
    display: flex;
    position: fixed;
    right: 0;
    top: 0;
    bottom: 0;
    width: 320px;
    background: linear-gradient(180deg, #1e1a3a 0%, #16213e 100%);
    border-left: 2px solid rgba(155, 89, 182, 0.4);
    z-index: 150;
    flex-direction: column;
    box-shadow: -8px 0 30px rgba(0,0,0,0.5);
  }}
  
  .group-panel-header {{
    padding: 20px 16px 12px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
  }}
  .group-panel-header h3 {{
    color: #bb8fce;
    margin: 0 0 10px;
    font-size: 16px;
  }}
  .group-panel-header .gp-hint {{
    color: #888;
    font-size: 12px;
    margin: 0 0 10px;
  }}
  .group-panel-header input {{
    width: 100%;
    padding: 8px 10px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(155, 89, 182, 0.4);
    border-radius: 6px;
    color: #e0e0e0;
    font-size: 13px;
    box-sizing: border-box;
  }}
  .group-panel-header input:focus {{
    outline: none;
    border-color: #bb8fce;
  }}
  
  .group-panel-body {{
    flex: 1;
    overflow-y: auto;
    padding: 12px 16px;
  }}
  .group-panel-body .empty-hint {{
    color: #666;
    font-size: 13px;
    text-align: center;
    margin-top: 40px;
    line-height: 1.8;
  }}
  .group-panel-body .gp-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 10px;
    background: rgba(155, 89, 182, 0.1);
    border-radius: 8px;
    margin-bottom: 6px;
    font-size: 13px;
    color: #ccc;
  }}
  .gp-item .gp-num {{
    flex-shrink: 0;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: rgba(155, 89, 182, 0.3);
    color: #bb8fce;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
  }}
  .gp-item .gp-title {{
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }}
  .gp-item .gp-remove {{
    cursor: pointer;
    opacity: 0.4;
    transition: opacity 0.2s;
    font-size: 14px;
  }}
  .gp-item .gp-remove:hover {{
    opacity: 1;
    color: #e74c3c;
  }}
  
  .group-panel-footer {{
    padding: 12px 16px;
    border-top: 1px solid rgba(255,255,255,0.1);
    display: flex;
    gap: 8px;
  }}
  .group-panel-footer button {{
    flex: 1;
    padding: 10px;
    border-radius: 8px;
    border: none;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
  }}
  .gp-btn-cancel {{
    background: rgba(255,255,255,0.08);
    color: #aaa;
  }}
  .gp-btn-cancel:hover {{ background: rgba(255,255,255,0.15); }}
  .gp-btn-save {{
    background: linear-gradient(135deg, #9b59b6, #8e44ad);
    color: #fff;
  }}
  .gp-btn-save:hover {{ filter: brightness(1.2); }}
  .gp-btn-save:disabled {{ opacity: 0.4; cursor: not-allowed; filter: none; }}
  
  /* 已保存编组标记 */
  .badge.group-saved {{
    font-size: 11px;
    padding: 2px 8px;
    border-radius: 12px;
    white-space: nowrap;
    cursor: default;
  }}
  
  /* 已保存编组列表 */
  .saved-groups-bar {{
    padding: 6px 0;
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    align-items: center;
  }}
  .saved-groups-bar:empty {{ display: none; }}
  .saved-group-chip {{
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 4px 10px;
    border-radius: 14px;
    font-size: 12px;
    font-weight: 500;
    cursor: default;
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>📰 人民日报文章选择</h1>
    <div class="subtitle">{self.title} | 共 {total_articles} 篇文章，{available_articles} 篇可选择</div>
  </div>
  
  <div class="toolbar">
    <div class="left">
      <button onclick="selectAll()">全选</button>
      <button onclick="deselectAll()">全不选</button>
      <button onclick="invertAll()">反选</button>
    </div>
    <div class="selected-count">已选 <span id="count">0</span> 篇</div>
  </div>
  <div class="saved-groups-bar" id="savedGroupsBar"></div>
  
  {content_html}
</div>

<div class="group-panel" id="groupPanel">
  <div class="group-panel-header">
    <h3>🔗 文章编组</h3>
    <p class="gp-hint">点击文章行末尾的 + 按钮加入编组</p>
    <input type="text" id="groupNameInput" placeholder="编组名称...">
  </div>
  <div class="group-panel-body" id="groupPanelBody">
    <div class="empty-hint">👈 点击左侧文章行末尾的 <b style="color:#bb8fce;font-size:16px">+</b> 按钮<br>将文章加入当前编组</div>
  </div>
  <div class="group-panel-footer">
    <button class="gp-btn-cancel" onclick="clearGroup()">清空</button>
    <button class="gp-btn-save" id="gpBtnSave" onclick="saveGroup()" disabled>保存编组 (0)</button>
  </div>
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
  
  document.querySelectorAll('.article-item:not(.skipped)').forEach(el => {{
    const cb = el.querySelector('.article-cb');
    if (cb) el.classList.toggle('selected', cb.checked);
  }});
  
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

document.querySelectorAll('.section-all-cb').forEach(allCb => {{
  allCb.addEventListener('change', function() {{
    const section = this.closest('.section');
    section.querySelectorAll('.article-cb').forEach(cb => {{
      cb.checked = allCb.checked;
    }});
    updateCount();
  }});
}});

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
  
  // 收集手动编组信息
  const groups = [];
  if (window._manualGroups) {{
    window._manualGroups.forEach(g => {{
      groups.push({{ name: g.name, article_indices: g.indices }});
    }});
  }}
  
  fetch('/', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ selected: selected, groups: groups }})
  }}).then(() => {{
    document.getElementById('doneOverlay').classList.add('show');
  }});
}}

// ====== 系列文章联动 ======
window._manualGroups = [];

document.querySelectorAll('.article-cb').forEach(cb => {{
  cb.addEventListener('change', function() {{
    if (!this.checked) return;
    const item = this.closest('.article-item');
    const seriesId = item ? item.getAttribute('data-series') : null;
    if (!seriesId) return;
    
    const siblings = document.querySelectorAll(`.article-item[data-series="${{seriesId}}"] .article-cb:not(:checked)`);
    if (siblings.length === 0) return;
    
    const seriesBadge = item.querySelector('.badge.series');
    const seriesName = seriesBadge ? seriesBadge.textContent.replace('🔗 ', '') : '该系列';
    
    if (confirm(`该文章属于系列「${{seriesName}}」，还有 ${{siblings.length}} 篇相关文章未选。\n是否全选该系列？`)) {{
      siblings.forEach(s => s.checked = true);
      updateCount();
    }}
  }});
}});

// ====== 编组（常驻） ======
const _GROUP_COLORS = ['#e74c3c','#3498db','#2ecc71','#9b59b6','#e67e22','#1abc9c','#f39c12','#e84393'];
let _currentGroupItems = [];  // [{{ idx, title }}]

function _generateGroupName() {{
  const now = new Date();
  const ts = now.getFullYear().toString() +
    String(now.getMonth()+1).padStart(2,'0') +
    String(now.getDate()).padStart(2,'0') + '_' +
    String(now.getHours()).padStart(2,'0') +
    String(now.getMinutes()).padStart(2,'0');
  const seq = String(window._manualGroups.length + 1).padStart(2, '0');
  return `编组_${{ts}}_${{seq}}`;
}}

// 页面加载时自动初始化
(function initGroupUI() {{
  document.getElementById('groupNameInput').value = _generateGroupName();
  
  document.querySelectorAll('.article-item:not(.skipped)').forEach(el => {{
    const cb = el.querySelector('.article-cb');
    if (!cb) return;
    const idx = parseInt(cb.value);
    const titleEl = el.querySelector('.title');
    const title = titleEl ? titleEl.textContent : '';
    
    const btn = document.createElement('span');
    btn.className = 'group-toggle-btn';
    btn.textContent = '+';
    btn.addEventListener('click', function(e) {{
      e.stopPropagation();
      e.preventDefault();
      toggleGroupItem(idx, title, el, btn);
    }});
    el.appendChild(btn);
  }});
}})();

function toggleGroupItem(idx, title, el, btn) {{
  const existIdx = _currentGroupItems.findIndex(g => g.idx === idx);
  if (existIdx >= 0) {{
    _currentGroupItems.splice(existIdx, 1);
    el.classList.remove('in-group');
    btn.textContent = '+';
    btn.classList.remove('added');
  }} else {{
    _currentGroupItems.push({{ idx, title }});
    el.classList.add('in-group');
    btn.textContent = '\u2212';
    btn.classList.add('added');
  }}
  renderGroupPanel();
}}

function clearGroup() {{
  document.querySelectorAll('.article-item.in-group').forEach(el => el.classList.remove('in-group'));
  document.querySelectorAll('.group-toggle-btn.added').forEach(btn => {{
    btn.textContent = '+';
    btn.classList.remove('added');
  }});
  _currentGroupItems = [];
  document.getElementById('groupNameInput').value = _generateGroupName();
  renderGroupPanel();
}}

function removeFromGroup(idx) {{
  _currentGroupItems = _currentGroupItems.filter(g => g.idx !== idx);
  document.querySelectorAll('.article-item:not(.skipped)').forEach(el => {{
    const cb = el.querySelector('.article-cb');
    if (cb && parseInt(cb.value) === idx) {{
      el.classList.remove('in-group');
      const btn = el.querySelector('.group-toggle-btn');
      if (btn) {{ btn.textContent = '+'; btn.classList.remove('added'); }}
    }}
  }});
  renderGroupPanel();
}}

function renderGroupPanel() {{
  const body = document.getElementById('groupPanelBody');
  const btn = document.getElementById('gpBtnSave');
  
  if (_currentGroupItems.length === 0) {{
    body.innerHTML = '<div class="empty-hint">👈 点击左侧文章行末尾的 <b style="color:#bb8fce;font-size:16px">+</b> 按钮<br>将文章加入当前编组</div>';
    btn.disabled = true;
    btn.textContent = '保存编组 (0)';
    return;
  }}
  
  btn.disabled = _currentGroupItems.length < 2;
  btn.textContent = `保存编组 (${{_currentGroupItems.length}})`;
  
  body.innerHTML = _currentGroupItems.map((g, i) => `
    <div class="gp-item">
      <span class="gp-num">${{i+1}}</span>
      <span class="gp-title">${{g.title}}</span>
      <span class="gp-remove" onclick="removeFromGroup(${{g.idx}})">\u2715</span>
    </div>
  `).join('');
}}

function saveGroup() {{
  if (_currentGroupItems.length < 2) return;
  const name = document.getElementById('groupNameInput').value.trim();
  if (!name) {{ alert('请输入编组名称'); return; }}
  
  const indices = _currentGroupItems.map(g => g.idx);
  const colorIdx = window._manualGroups.length % _GROUP_COLORS.length;
  const color = _GROUP_COLORS[colorIdx];
  
  window._manualGroups.push({{ name, indices, color }});
  
  document.querySelectorAll('.article-item:not(.skipped)').forEach(el => {{
    const cb = el.querySelector('.article-cb');
    if (!cb) return;
    const idx = parseInt(cb.value);
    if (indices.includes(idx)) {{
      const badge = document.createElement('span');
      badge.className = 'badge group-saved';
      badge.style.cssText = `background:${{color}}20;color:${{color}};border:1px solid ${{color}}40`;
      badge.textContent = '🔗 ' + name;
      el.appendChild(badge);
      el.style.borderLeft = `4px solid ${{color}}`;
      cb.checked = true;
    }}
  }});
  updateCount();
  
  renderSavedGroupsBar();
  clearGroup();
}}

function renderSavedGroupsBar() {{
  const bar = document.getElementById('savedGroupsBar');
  bar.innerHTML = window._manualGroups.map((g, i) => {{
    return `<span class="saved-group-chip" style="background:${{g.color}}20;color:${{g.color}};border:1px solid ${{g.color}}40">🔗 ${{g.name}} (${{g.indices.length}}篇)</span>`;
  }}).join('');
}}
</script>
</body>
</html>'''
