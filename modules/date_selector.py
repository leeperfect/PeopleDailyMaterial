#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web UI 日期选择器 - 本地浏览器界面，选择要下载的日期/日期范围
固定显示近两年（当年+去年）的月历，标记已完成下载并同步 Notion 的日期
默认连续选择模式，单日选择作为备选
"""

import json
import logging
import os
import webbrowser
import threading
import socket
import calendar
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Tuple, Set


# ====== 同步状态追踪 ======
SYNC_STATUS_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'sync_status.json')


def load_synced_dates() -> Set[str]:
    """加载已完成同步的日期集合，格式 {'2026-01-01', '2026-01-02', ...}"""
    try:
        if os.path.exists(SYNC_STATUS_FILE):
            with open(SYNC_STATUS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get('synced_dates', []))
    except Exception as e:
        logging.error(f"加载同步状态失败: {e}")
    return set()


def save_synced_dates(dates: Set[str]):
    """保存已完成同步的日期集合"""
    try:
        os.makedirs(os.path.dirname(SYNC_STATUS_FILE), exist_ok=True)
        with open(SYNC_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump({'synced_dates': sorted(dates)}, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"保存同步状态失败: {e}")


def mark_date_synced(date_str: str):
    """标记某日期已完成本地下载+Notion同步"""
    dates = load_synced_dates()
    dates.add(date_str)
    save_synced_dates(dates)


def get_downloaded_dates() -> Set[str]:
    """检查 data/raw/ 目录中已有本地下载文件的日期"""
    raw_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'raw')
    downloaded = set()
    if os.path.exists(raw_dir):
        for fname in os.listdir(raw_dir):
            # articles_20260101.json -> 2026-01-01
            if fname.startswith('articles_') and fname.endswith('.json'):
                date_part = fname[9:17]  # YYYYMMDD
                if len(date_part) == 8 and date_part.isdigit():
                    formatted = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
                    downloaded.add(formatted)
    return downloaded


class DateSelector:
    """通过本地 Web 页面让用户选择日期或日期范围"""

    def __init__(self):
        self.start_date: Optional[datetime] = None
        self.end_date: Optional[datetime] = None
        self.selection_done = threading.Event()
        self.server = None

    def show_and_wait(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """启动 Web 界面并等待用户选择，返回 (start_date, end_date)"""
        handler = self._make_handler()
        
        start_port = 18764
        max_attempts = 20
        port = start_port
        
        for attempt in range(max_attempts):
            try:
                self.server = HTTPServer(('127.0.0.1', port), handler)
                self.server.allow_reuse_address = True
                self.server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                break
            except OSError as e:
                if e.errno == 48 or 'Address already in use' in str(e):
                    port += 1
                    continue
                raise
        else:
            raise RuntimeError(f"无法找到可用端口 (尝试了 {start_port} ~ {port})")

        server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        server_thread.start()

        url = f'http://127.0.0.1:{port}'
        print(f"\n  🌐 已打开日期选择页面: {url}")
        print(f"  📅 请在浏览器中选择要下载的日期，然后点击「确认」按钮")
        print(f"  ⏳ 等待你的选择...\n")

        webbrowser.open(url)

        self.selection_done.wait()
        self.server.shutdown()

        return self.start_date, self.end_date

    def _make_handler(self):
        selector = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

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
                    start_str = data.get('start_date', '')
                    end_str = data.get('end_date', '')

                    if start_str:
                        selector.start_date = datetime.strptime(start_str, '%Y-%m-%d')
                    if end_str:
                        selector.end_date = datetime.strptime(end_str, '%Y-%m-%d')
                    else:
                        selector.end_date = None
                except Exception as e:
                    logging.error(f"解析日期失败: {e}")
                    selector.start_date = None
                    selector.end_date = None

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': True}).encode('utf-8'))

                selector.selection_done.set()

        return Handler

    def _build_calendar_html(self) -> str:
        """生成当年+去年（共两年）的月历 HTML，并标记已下载/同步的日期"""
        today = datetime.now()
        today_str = today.strftime('%Y-%m-%d')
        
        # 加载状态数据
        synced_dates = load_synced_dates()
        downloaded_dates = get_downloaded_dates()
        
        current_year = today.year
        prev_year = current_year - 1
        
        month_names = ['一月', '二月', '三月', '四月', '五月', '六月',
                       '七月', '八月', '九月', '十月', '十一月', '十二月']
        
        months_html = ''
        
        # 按年份从近到远排列：先当年，再去年
        for year in [current_year, prev_year]:
            # 添加年份标题
            is_current_year = (year == current_year)
            year_cls = 'current-year' if is_current_year else ''
            months_html += f'''
            <div class="year-divider {year_cls}">
                <span class="year-label">{year}年</span>
                <span class="year-line"></span>
            </div>'''
            
            # 当年显示到当前月，去年显示全部12个月
            max_month = today.month if is_current_year else 12
            
            for m in range(max_month, 0, -1):
                month_label = f'{month_names[m - 1]}'
                is_current_month = (year == today.year and m == today.month)
                
                # 获取该月的天数和起始星期几（周一=0）
                _, days_in_month = calendar.monthrange(year, m)
                first_weekday = calendar.weekday(year, m, 1)  # 0=Monday
                
                # 构建日期格子
                cells_html = ''
                # 填充前面的空格
                for _ in range(first_weekday):
                    cells_html += '<div class="cal-cell empty"></div>'
                
                for day in range(1, days_in_month + 1):
                    d = datetime(year, m, day)
                    date_str = d.strftime('%Y-%m-%d')
                    is_weekend = d.weekday() >= 5
                    is_today = (date_str == today_str)
                    is_future = d > today
                    
                    # 检查下载/同步状态
                    is_synced = (date_str in synced_dates)
                    is_downloaded = (date_str in downloaded_dates)
                    
                    cls = 'cal-cell'
                    if is_future:
                        cls += ' future'
                    elif is_today:
                        cls += ' today'
                    elif is_weekend:
                        cls += ' weekend'
                    
                    if is_synced:
                        cls += ' synced'
                    elif is_downloaded:
                        cls += ' downloaded-only'
                    
                    if is_future:
                        cells_html += f'<div class="{cls}"><span>{day}</span></div>'
                    else:
                        # 添加状态图标
                        status_icon = ''
                        if is_synced:
                            status_icon = '<span class="status-dot synced-dot" title="已下载并同步"></span>'
                        elif is_downloaded:
                            status_icon = '<span class="status-dot dl-dot" title="仅本地下载，未同步Notion"></span>'
                        
                        cells_html += f'<div class="{cls}" data-date="{date_str}" onclick="calSelect(\'{date_str}\')">{status_icon}<span>{day}</span></div>'
                
                cur_cls = ' current-month' if is_current_month else ''
                months_html += f'''
                <div class="cal-month{cur_cls}">
                    <div class="cal-month-title">{month_label}</div>
                    <div class="cal-weekdays">
                        <span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span class="we">六</span><span class="we">日</span>
                    </div>
                    <div class="cal-grid">{cells_html}</div>
                </div>'''
        
        return months_html

    def _generate_html(self) -> str:
        """生成文章选择页面 HTML"""
        today = datetime.now()
        today_str = today.strftime('%Y-%m-%d')
        current_year = today.year
        prev_year = current_year - 1
        min_date = f'{prev_year}-01-01'

        calendar_html = self._build_calendar_html()
        
        # 统计已同步的日期数量
        synced_dates = load_synced_dates()
        downloaded_dates = get_downloaded_dates()
        synced_count = len(synced_dates)
        downloaded_only_count = len(downloaded_dates - synced_dates)

        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>人民日报 - 选择下载日期</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700&display=swap');

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
    color: #e0e0e0;
    display: flex;
    justify-content: center;
    align-items: flex-start;
    padding: 30px 20px 120px;
  }}

  .container {{
    max-width: 960px;
    width: 100%;
  }}

  .header {{
    text-align: center;
    margin-bottom: 28px;
  }}

  .header h1 {{
    font-size: 30px;
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

  /* ====== 状态统计条 ====== */
  .stats-bar {{
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-bottom: 20px;
  }}

  .stat-item {{
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: #999;
    background: rgba(255,255,255,0.04);
    padding: 6px 14px;
    border-radius: 20px;
    border: 1px solid rgba(255,255,255,0.06);
  }}

  .stat-dot {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
  }}

  .stat-dot.synced {{ background: #2ecc71; box-shadow: 0 0 6px rgba(46,204,113,0.4); }}
  .stat-dot.dl-only {{ background: #f39c12; box-shadow: 0 0 6px rgba(243,156,18,0.4); }}
  .stat-dot.pending {{ background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.25); }}

  /* ====== 模式切换 ====== */
  .mode-switch {{
    display: flex;
    justify-content: center;
    gap: 0;
    margin-bottom: 20px;
    background: rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 4px;
    border: 1px solid rgba(255,255,255,0.08);
    max-width: 400px;
    margin-left: auto;
    margin-right: auto;
  }}

  .mode-btn {{
    flex: 1;
    padding: 10px 20px;
    border: none;
    background: transparent;
    color: #888;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    border-radius: 10px;
    transition: all 0.3s;
    font-family: inherit;
  }}

  .mode-btn.active {{
    background: linear-gradient(135deg, rgba(247,151,30,0.2), rgba(255,210,0,0.15));
    color: #ffd200;
    box-shadow: 0 2px 12px rgba(247,151,30,0.15);
  }}

  .mode-btn:hover:not(.active) {{
    color: #ccc;
    background: rgba(255,255,255,0.04);
  }}

  /* ====== 提示文字 ====== */
  .mode-hint {{
    text-align: center;
    color: #777;
    font-size: 13px;
    margin-bottom: 20px;
    min-height: 20px;
    transition: all 0.3s;
  }}

  /* ====== 年份分隔 ====== */
  .year-divider {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 24px 0 16px;
    padding: 0 4px;
  }}

  .year-divider:first-child {{
    margin-top: 0;
  }}

  .year-label {{
    font-size: 18px;
    font-weight: 700;
    color: #888;
    white-space: nowrap;
    letter-spacing: 2px;
  }}

  .year-divider.current-year .year-label {{
    color: #ffd200;
  }}

  .year-line {{
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(255,255,255,0.15), transparent);
  }}

  /* ====== 月历面板 ====== */
  .panel {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 20px;
  }}

  .panel-title {{
    font-size: 15px;
    font-weight: 600;
    color: #bbb;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}

  /* 月历网格：4列（两年各6行 * 2列 = 更紧凑） */
  .cal-container {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
  }}

  .cal-month {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 12px;
    transition: border-color 0.2s;
  }}

  .cal-month.current-month {{
    border-color: rgba(247,151,30,0.3);
    background: rgba(247,151,30,0.03);
  }}

  .cal-month-title {{
    text-align: center;
    font-size: 13px;
    font-weight: 600;
    color: #ccc;
    margin-bottom: 8px;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }}

  .current-month .cal-month-title {{
    color: #ffd200;
  }}

  .cal-weekdays {{
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    text-align: center;
    font-size: 10px;
    color: #666;
    margin-bottom: 4px;
  }}

  .cal-weekdays .we {{
    color: #a0555588;
  }}

  .cal-grid {{
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 2px;
  }}

  .cal-cell {{
    aspect-ratio: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.15s;
    position: relative;
    color: #ccc;
  }}

  .cal-cell:hover:not(.empty):not(.future) {{
    background: rgba(255,255,255,0.12);
    transform: scale(1.1);
    z-index: 2;
  }}

  .cal-cell.empty {{
    cursor: default;
  }}

  .cal-cell.future {{
    color: #444;
    cursor: not-allowed;
    opacity: 0.4;
  }}

  .cal-cell.today {{
    color: #2ecc71;
    font-weight: 700;
    border: 1px solid rgba(46,204,113,0.4);
  }}

  .cal-cell.weekend {{
    color: #b0707088;
  }}

  /* ====== 下载/同步状态标记 ====== */
  .status-dot {{
    position: absolute;
    top: 2px;
    right: 2px;
    width: 5px;
    height: 5px;
    border-radius: 50%;
    pointer-events: none;
  }}

  .synced-dot {{
    background: #2ecc71;
    box-shadow: 0 0 4px rgba(46,204,113,0.5);
  }}

  .dl-dot {{
    background: #f39c12;
    box-shadow: 0 0 4px rgba(243,156,18,0.5);
  }}

  .cal-cell.synced {{
    border: 1px solid rgba(46,204,113,0.25);
  }}

  .cal-cell.downloaded-only {{
    border: 1px solid rgba(243,156,18,0.2);
  }}

  /* 选中态 */
  .cal-cell.selected {{
    background: rgba(247,151,30,0.35) !important;
    color: #ffd200 !important;
    font-weight: 700;
    border-radius: 6px;
    box-shadow: 0 0 8px rgba(247,151,30,0.3);
  }}

  .cal-cell.range-start {{
    background: rgba(247,151,30,0.4) !important;
    color: #ffd200 !important;
    font-weight: 700;
    border-radius: 6px 3px 3px 6px;
    box-shadow: 0 0 8px rgba(247,151,30,0.3);
  }}

  .cal-cell.range-end {{
    background: rgba(247,151,30,0.4) !important;
    color: #ffd200 !important;
    font-weight: 700;
    border-radius: 3px 6px 6px 3px;
    box-shadow: 0 0 8px rgba(247,151,30,0.3);
  }}

  .cal-cell.range-mid {{
    background: rgba(247,151,30,0.12) !important;
    color: #f0c060 !important;
    border-radius: 2px;
  }}

  /* ====== 手动输入 ====== */
  .manual-section {{
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid rgba(255,255,255,0.06);
  }}

  .date-input-row {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 10px;
  }}

  .date-input-row label {{
    font-size: 13px;
    color: #999;
    white-space: nowrap;
    min-width: 50px;
  }}

  .date-input-row input[type="date"] {{
    flex: 1;
    padding: 8px 12px;
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 8px;
    color: #e0e0e0;
    font-size: 14px;
    font-family: inherit;
    transition: border-color 0.2s;
    max-width: 280px;
  }}

  .date-input-row input[type="date"]:focus {{
    outline: none;
    border-color: #f7971e;
    box-shadow: 0 0 0 3px rgba(247,151,30,0.15);
  }}

  .date-input-row input[type="date"]::-webkit-calendar-picker-indicator {{
    filter: invert(0.7);
    cursor: pointer;
  }}

  .arrow {{
    color: #666;
    font-size: 18px;
  }}

  /* ====== 预览 + 操作 ====== */
  .bottom-bar {{
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    padding: 14px 24px;
    background: rgba(15, 12, 41, 0.95);
    backdrop-filter: blur(20px);
    border-top: 1px solid rgba(255,255,255,0.1);
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 20px;
    z-index: 100;
  }}

  .preview-text {{
    font-size: 15px;
    color: #ffd200;
    font-weight: 500;
  }}

  .preview-text.empty {{
    color: #666;
  }}

  .preview-days {{
    font-size: 12px;
    color: #f7971e;
    background: rgba(247,151,30,0.15);
    padding: 3px 10px;
    border-radius: 20px;
    margin-left: 8px;
  }}

  .btn {{
    padding: 11px 36px;
    border: none;
    border-radius: 10px;
    font-size: 15px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.3s;
    font-family: inherit;
  }}

  .btn-confirm {{
    background: linear-gradient(90deg, #f7971e, #ffd200);
    color: #1a1a2e;
    box-shadow: 0 4px 15px rgba(247,151,30,0.3);
  }}

  .btn-confirm:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 25px rgba(247,151,30,0.5);
  }}

  .btn-confirm:disabled {{
    opacity: 0.35;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }}

  .btn-reset {{
    padding: 11px 20px;
    background: rgba(255,255,255,0.08);
    color: #999;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 10px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
    font-family: inherit;
  }}

  .btn-reset:hover {{
    background: rgba(255,255,255,0.15);
    color: #ccc;
  }}

  /* ====== 完成遮罩 ====== */
  .done-overlay {{
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(15, 12, 41, 0.92);
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
    font-size: 22px;
    color: #ffd200;
    font-weight: 600;
  }}

  .done-overlay .subtext {{
    color: #888;
    font-size: 14px;
  }}

  .hidden {{
    display: none !important;
  }}

  /* ====== 手动输入分隔线 ====== */
  .divider {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 12px 0 8px;
    color: #555;
    font-size: 12px;
  }}
  .divider::before, .divider::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(255,255,255,0.06);
  }}

  /* 响应式 */
  @media (max-width: 900px) {{
    .cal-container {{
      grid-template-columns: repeat(3, 1fr);
    }}
  }}

  @media (max-width: 600px) {{
    .cal-container {{
      grid-template-columns: repeat(2, 1fr);
    }}
  }}

  @media (max-width: 400px) {{
    .cal-container {{
      grid-template-columns: 1fr;
    }}
  }}
</style>
</head>
<body>

<div class="container">
  <div class="header">
    <h1>📰 人民日报素材系统</h1>
    <div class="subtitle">选择要下载的日期，支持连续日期范围或单日选择 · {prev_year}年 ~ {current_year}年</div>
  </div>

  <!-- 状态统计 -->
  <div class="stats-bar">
    <div class="stat-item">
      <span class="stat-dot synced"></span>
      已同步 {synced_count} 天
    </div>
    <div class="stat-item">
      <span class="stat-dot dl-only"></span>
      仅下载 {downloaded_only_count} 天
    </div>
    <div class="stat-item">
      <span class="stat-dot pending"></span>
      未下载
    </div>
  </div>

  <!-- 模式切换：默认连续选择 -->
  <div class="mode-switch">
    <button class="mode-btn" id="modeSingle" onclick="switchMode('single')">📅 单日下载</button>
    <button class="mode-btn active" id="modeRange" onclick="switchMode('range')">📆 连续选择</button>
  </div>

  <div class="mode-hint" id="modeHint">第一次点击选择起始日期，第二次点击选择结束日期</div>

  <!-- 月历面板 -->
  <div class="panel">
    <div class="panel-title">📆 {prev_year} ~ {current_year} 年月历（点击日期选择）</div>
    <div class="cal-container">
      {calendar_html}
    </div>

    <div class="divider">或手动输入日期</div>
    <div class="date-input-row">
      <label id="startLabel">起始</label>
      <input type="date" id="startDate" value="" min="{min_date}" max="{today_str}">
      <span class="arrow" id="inputArrow">→</span>
      <label id="endLabel">至</label>
      <input type="date" id="endDate" min="{min_date}" max="{today_str}">
    </div>
  </div>
</div>

<!-- 底部操作栏 -->
<div class="bottom-bar">
  <span class="preview-text empty" id="previewText">请选择日期</span>
  <span class="preview-days hidden" id="previewDays"></span>
  <button class="btn-reset" onclick="resetSelection()">重置</button>
  <button class="btn btn-confirm" id="btnConfirm" onclick="submitSelection()" disabled>确认并获取文章列表</button>
</div>

<!-- 完成遮罩 -->
<div class="done-overlay" id="doneOverlay">
  <div class="icon">✅</div>
  <div class="text">日期已确认！</div>
  <div class="subtext">正在获取文章列表，请回到终端查看进度...</div>
</div>

<script>
  // 默认模式：连续选择（range）
  let mode = 'range';
  let selectedStart = '';
  let selectedEnd = '';
  let rangeClickCount = 0;

  function switchMode(m) {{
    mode = m;
    document.getElementById('modeSingle').classList.toggle('active', m === 'single');
    document.getElementById('modeRange').classList.toggle('active', m === 'range');

    // 切换手动输入区显示
    const showRange = (m === 'range');
    document.getElementById('startLabel').textContent = showRange ? '起始' : '日期';
    document.getElementById('inputArrow').classList.toggle('hidden', !showRange);
    document.getElementById('endLabel').classList.toggle('hidden', !showRange);
    document.getElementById('endDate').classList.toggle('hidden', !showRange);

    // 更新提示
    if (m === 'single') {{
      document.getElementById('modeHint').textContent = '点击日历中的日期即可选择';
    }} else {{
      document.getElementById('modeHint').textContent = '第一次点击选择起始日期，第二次点击选择结束日期';
    }}

    rangeClickCount = 0;
    selectedEnd = '';
    document.getElementById('endDate').value = '';
    clearAllHighlights();
    if (selectedStart) {{
      highlightSingle(selectedStart);
    }}
    updatePreview();
  }}

  function calSelect(dateStr) {{
    if (mode === 'single') {{
      clearAllHighlights();
      selectedStart = dateStr;
      selectedEnd = '';
      document.getElementById('startDate').value = dateStr;
      highlightSingle(dateStr);
    }} else {{
      rangeClickCount++;
      if (rangeClickCount === 1) {{
        clearAllHighlights();
        selectedStart = dateStr;
        selectedEnd = '';
        document.getElementById('startDate').value = dateStr;
        document.getElementById('endDate').value = '';
        highlightSingle(dateStr);
        document.getElementById('modeHint').textContent = '✓ 已选起始日期，请点击结束日期';
      }} else {{
        rangeClickCount = 0;
        selectedEnd = dateStr;
        if (selectedStart > selectedEnd) {{
          [selectedStart, selectedEnd] = [selectedEnd, selectedStart];
        }}
        document.getElementById('startDate').value = selectedStart;
        document.getElementById('endDate').value = selectedEnd;
        highlightRange(selectedStart, selectedEnd);
        document.getElementById('modeHint').textContent = '第一次点击选择起始日期，第二次点击选择结束日期';
      }}
    }}
    updatePreview();
  }}

  function clearAllHighlights() {{
    document.querySelectorAll('.cal-cell').forEach(el => {{
      el.classList.remove('selected', 'range-start', 'range-end', 'range-mid');
    }});
  }}

  function highlightSingle(dateStr) {{
    document.querySelectorAll('.cal-cell[data-date="' + dateStr + '"]').forEach(el => {{
      el.classList.add('selected');
    }});
  }}

  function highlightRange(start, end) {{
    clearAllHighlights();
    document.querySelectorAll('.cal-cell[data-date]').forEach(el => {{
      const d = el.dataset.date;
      if (d === start) {{
        el.classList.add('range-start');
      }} else if (d === end) {{
        el.classList.add('range-end');
      }} else if (d > start && d < end) {{
        el.classList.add('range-mid');
      }}
    }});
  }}

  function updatePreview() {{
    const previewText = document.getElementById('previewText');
    const previewDays = document.getElementById('previewDays');
    const btn = document.getElementById('btnConfirm');

    if (!selectedStart) {{
      previewText.textContent = '请选择日期';
      previewText.classList.add('empty');
      previewDays.classList.add('hidden');
      btn.disabled = true;
      return;
    }}

    previewText.classList.remove('empty');

    if (mode === 'single' || !selectedEnd) {{
      previewText.textContent = '📅 ' + selectedStart;
      previewDays.textContent = '1 天';
      previewDays.classList.remove('hidden');
      btn.disabled = false;
    }} else {{
      const s = new Date(selectedStart);
      const e = new Date(selectedEnd);
      const days = Math.round((e - s) / (1000 * 60 * 60 * 24)) + 1;
      previewText.textContent = '📅 ' + selectedStart + '  →  ' + selectedEnd;
      previewDays.textContent = days + ' 天';
      previewDays.classList.remove('hidden');
      btn.disabled = false;
    }}
  }}

  function resetSelection() {{
    selectedStart = '';
    selectedEnd = '';
    rangeClickCount = 0;
    document.getElementById('startDate').value = '';
    document.getElementById('endDate').value = '';
    clearAllHighlights();
    updatePreview();
    if (mode === 'range') {{
      document.getElementById('modeHint').textContent = '第一次点击选择起始日期，第二次点击选择结束日期';
    }}
  }}

  // 监听手动输入
  document.getElementById('startDate').addEventListener('change', function() {{
    selectedStart = this.value;
    rangeClickCount = 0;
    clearAllHighlights();
    if (mode === 'single') {{
      selectedEnd = '';
      highlightSingle(selectedStart);
    }} else if (selectedEnd) {{
      if (selectedStart > selectedEnd) {{
        [selectedStart, selectedEnd] = [selectedEnd, selectedStart];
        document.getElementById('startDate').value = selectedStart;
        document.getElementById('endDate').value = selectedEnd;
      }}
      highlightRange(selectedStart, selectedEnd);
    }} else {{
      highlightSingle(selectedStart);
    }}
    updatePreview();
  }});

  document.getElementById('endDate').addEventListener('change', function() {{
    selectedEnd = this.value;
    rangeClickCount = 0;
    if (selectedStart && selectedEnd && selectedStart > selectedEnd) {{
      [selectedStart, selectedEnd] = [selectedEnd, selectedStart];
      document.getElementById('startDate').value = selectedStart;
      document.getElementById('endDate').value = selectedEnd;
    }}
    clearAllHighlights();
    if (selectedStart && selectedEnd) {{
      highlightRange(selectedStart, selectedEnd);
    }}
    updatePreview();
  }});

  function submitSelection() {{
    const payload = {{
      start_date: selectedStart,
      end_date: (mode === 'range' && selectedEnd) ? selectedEnd : ''
    }};

    fetch('/', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify(payload)
    }}).then(() => {{
      document.getElementById('doneOverlay').classList.add('show');
    }});
  }}

  // 初始化
  updatePreview();
</script>
</body>
</html>'''
