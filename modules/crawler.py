#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爬虫模块 - 双模式：requests.Session（目录页）+ Playwright stealth（文章页反爬）

核心设计：
1. 目录页使用 requests.Session 同步抓取 —— 稳定可靠，无 event loop 问题
2. 文章页使用 Playwright + stealth 注入 —— 绕过高强度反爬
3. Cookie 在两个通道间共享，降低被检测概率
4. 全面的反爬特性：UA 轮换、随机延迟、指纹隐藏、鼠标模拟、Canvas 保护
"""

import re
import time
import random
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import requests as req_lib

from modules.utils import Config


# ========== User-Agent 池（现代 Chrome 版本） ==========
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
]


# ========== Stealth JavaScript（注入到 Playwright 的反检测脚本） ==========
STEALTH_JS = """
// ===== 1. 隐藏 webdriver 标志 =====
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
delete navigator.__proto__.webdriver;

// ===== 2. 模拟真实 Chrome 运行时 =====
window.chrome = {
    runtime: {
        PlatformOs: { MAC: 'mac', WIN: 'win', ANDROID: 'android', CROS: 'cros', LINUX: 'linux', OPENBSD: 'openbsd' },
        PlatformArch: { ARM: 'arm', X86_32: 'x86-32', X86_64: 'x86-64', MIPS: 'mips', MIPS64: 'mips64' },
        PlatformNaclArch: { ARM: 'arm', X86_32: 'x86-32', X86_64: 'x86-64', MIPS: 'mips', MIPS64: 'mips64' },
        RequestUpdateCheckStatus: { THROTTLED: 'throttled', NO_UPDATE: 'no_update', UPDATE_AVAILABLE: 'update_available' },
        OnInstalledReason: { INSTALL: 'install', UPDATE: 'update', CHROME_UPDATE: 'chrome_update', SHARED_MODULE_UPDATE: 'shared_module_update' },
        OnRestartRequiredReason: { APP_UPDATE: 'app_update', OS_UPDATE: 'os_update', PERIODIC: 'periodic' },
    },
    loadTimes: function() { return {}; },
    csi: function() { return {}; },
    app: { isInstalled: false, InstallState: { DISABLED: 'disabled', INSTALLED: 'installed', NOT_INSTALLED: 'not_installed' }, RunningState: { CANNOT_RUN: 'cannot_run', READY_TO_RUN: 'ready_to_run', RUNNING: 'running' } },
};

// ===== 3. 模拟真实插件列表 =====
Object.defineProperty(navigator, 'plugins', {
    get: () => {
        const plugins = [
            { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
            { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
            { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
        ];
        plugins.refresh = () => {};
        return plugins;
    }
});

// ===== 4. 设置语言 =====
Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en-US', 'en'] });
Object.defineProperty(navigator, 'language', { get: () => 'zh-CN' });

// ===== 5. 隐藏自动化标志 =====
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);

// ===== 6. 模拟真实的 hardwareConcurrency =====
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });

// ===== 7. 模拟真实的 deviceMemory =====
Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });

// ===== 8. Canvas fingerprint 轻微扰动（不破坏渲染，但改变指纹哈希） =====
const _origToDataURL = HTMLCanvasElement.prototype.toDataURL;
HTMLCanvasElement.prototype.toDataURL = function(type) {
    if (type === 'image/png' || type === undefined) {
        const ctx = this.getContext('2d');
        if (ctx) {
            const imgData = ctx.getImageData(0, 0, this.width, this.height);
            for (let i = 0; i < imgData.data.length; i += 4) {
                imgData.data[i] = imgData.data[i] ^ 1;     // R
            }
            ctx.putImageData(imgData, 0, 0);
        }
    }
    return _origToDataURL.apply(this, arguments);
};

// ===== 9. WebGL vendor / renderer =====
const getParameter = WebGLRenderingContext.prototype.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) return 'Intel Inc.';
    if (parameter === 37446) return 'Intel Iris OpenGL Engine';
    return getParameter.apply(this, arguments);
};

// ===== 10. 隐藏 Playwright 特有的全局变量 =====
delete window.__playwright;
delete window.__pw_manual;
"""


class URLGenerator:
    """URL生成类"""
    def __init__(self):
        self.base_url = "https://paper.people.com.cn/rmrb/pc/layout/{date_str}/node_{node_id}.html"

    def generate_url(self, date: datetime, node_id: str = "01") -> str:
        date_str = date.strftime("%Y%m/%d")
        return self.base_url.format(date_str=date_str, node_id=node_id)


class RequestsFetcher:
    """requests.Session 同步抓取器（用于目录页）

    使用 requests.Session 保持 cookie、连接复用，
    简单可靠，不存在 event loop 问题。
    """

    def __init__(self, config: Config):
        self.session = req_lib.Session()
        self.max_retries = config.get('crawler.max_retries', 5)
        self.request_count = 0
        # 目录页不需要长间隔
        self.request_interval = [1.5, 4]

        # 配置 session 级别的 headers
        self._base_ua = random.choice(USER_AGENTS)
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
        })

        # 预热
        self._warmup()

    def _warmup(self):
        """预热 session，建立 cookie"""
        try:
            headers = {'User-Agent': self._base_ua, 'Referer': 'https://www.people.com.cn/'}
            self.session.get('https://paper.people.com.cn/', headers=headers, timeout=10)
            time.sleep(random.uniform(0.5, 1.5))
            self.session.get('https://paper.people.com.cn/rmrb/pc/', headers=headers, timeout=10)
            time.sleep(random.uniform(0.5, 1))
            logging.info("requests session 预热完成")
        except Exception as e:
            logging.warning(f"requests 预热失败: {e}")

    def _get_headers(self) -> dict:
        """每次请求轮换 UA 并携带合理的 Referer"""
        return {
            'User-Agent': random.choice(USER_AGENTS),
            'Referer': 'https://paper.people.com.cn/rmrb/pc/',
        }

    def get_page(self, url: str) -> Optional[str]:
        """获取页面内容"""
        retries = 0
        while retries < self.max_retries:
            try:
                self.request_count += 1
                sleep_time = random.uniform(*self.request_interval)
                time.sleep(sleep_time)

                response = self.session.get(url, headers=self._get_headers(), timeout=15)

                if response.status_code == 200:
                    response.encoding = 'utf-8'
                    return response.text
                elif response.status_code == 403:
                    retries += 1
                    wait = 8 * retries + random.uniform(0, 5)
                    logging.warning(f"目录页 403，等待 {wait:.0f}s 后重试: {url}")
                    time.sleep(wait)
                    # 403 后重新预热
                    self._warmup()
                    continue
                elif response.status_code == 404:
                    logging.warning(f"目录页 404（不存在）: {url}")
                    return None
                else:
                    retries += 1
                    logging.warning(f"目录页返回 {response.status_code}: {url}")

            except Exception as e:
                retries += 1
                wait = 3 * retries + random.uniform(0, 2)
                logging.warning(f"目录页请求失败 ({retries}/{self.max_retries}): {e}")
                time.sleep(wait)

        return None

    def get_cookies_dict(self) -> dict:
        """导出 cookie 供 Playwright 共享"""
        return dict(self.session.cookies)


class PlaywrightBrowser:
    """Playwright 浏览器管理类（stealth 模式，延迟初始化）

    核心反爬策略：
    - 完整的 stealth.js 注入（隐藏所有自动化痕迹）
    - 随机视口尺寸 + 真实设备像素比
    - 真实的鼠标移动和页面交互模拟
    - 每 N 次请求自动轮换 context（模拟新用户）
    - Cookie 从 requests session 共享，维持一致的会话身份
    """

    def __init__(self, config: Config):
        self.config = config
        self.request_interval = config.get('crawler.request_interval', [8, 15])
        self.max_retries = config.get('crawler.max_retries', 5)
        self.request_count = 0
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        # 每 15-25 次请求轮换 context
        self._rotate_threshold = random.randint(15, 25)

    def _is_alive(self) -> bool:
        """检查浏览器连接是否存活"""
        if self._page is None or self._browser is None:
            return False
        try:
            if self._page.is_closed():
                return False
            self._page.title()
            return True
        except Exception:
            logging.warning("检测到浏览器连接已断开")
            return False

    def _restart_browser(self):
        """强制关闭并重新启动浏览器"""
        logging.info("正在重启 Playwright 浏览器...")
        self._close_internal()
        self._ensure_browser()
        logging.info("Playwright 浏览器重启完成")

    def _rotate_context(self):
        """轮换浏览器 context（模拟新用户，清除指纹）"""
        logging.info("轮换浏览器 context 以避免指纹追踪...")
        try:
            if self._page and not self._page.is_closed():
                self._page.close()
            if self._context:
                self._context.close()
        except Exception:
            pass

        self._context = self._create_context()
        self._page = self._context.new_page()
        self._page.set_default_timeout(30000)
        self._warmup()
        self._rotate_threshold = random.randint(15, 25)
        self.request_count = 0

    def _random_viewport(self) -> dict:
        """生成随机但合理的视口尺寸"""
        viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1440, 'height': 900},
            {'width': 1536, 'height': 864},
            {'width': 1366, 'height': 768},
            {'width': 1680, 'height': 1050},
            {'width': 2560, 'height': 1440},
        ]
        return random.choice(viewports)

    def _create_context(self, cookies: Optional[List[dict]] = None):
        """创建新的浏览器上下文（带完整反检测配置）"""
        viewport = self._random_viewport()
        ua = random.choice(USER_AGENTS)

        context = self._browser.new_context(
            viewport=viewport,
            user_agent=ua,
            locale='zh-CN',
            timezone_id='Asia/Shanghai',
            color_scheme='light',
            device_scale_factor=random.choice([1, 1.25, 1.5, 2]),
            extra_http_headers={
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Sec-CH-UA': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                'Sec-CH-UA-Mobile': '?0',
                'Sec-CH-UA-Platform': '"macOS"',
            },
        )

        # 屏蔽图片/字体/媒体资源以加速（但保留 CSS/JS）
        context.route(
            "**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,eot,mp4,webm,ogg}",
            lambda route: route.abort()
        )

        # 注入 stealth 脚本
        context.add_init_script(STEALTH_JS)

        # 导入 cookies
        if cookies:
            context.add_cookies(cookies)

        return context

    def _ensure_browser(self, shared_cookies: Optional[dict] = None):
        """确保浏览器已启动（延迟初始化）"""
        if self._page is not None and not self._page.is_closed():
            return

        from playwright.sync_api import sync_playwright

        logging.info("正在启动 Playwright 浏览器（stealth 模式）...")

        self._playwright = sync_playwright().start()

        self._browser = self._playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process',
                '--lang=zh-CN',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-infobars',
                '--disable-extensions',
            ]
        )

        # 转换 shared_cookies 为 Playwright 格式
        pw_cookies = None
        if shared_cookies:
            pw_cookies = []
            for name, value in shared_cookies.items():
                pw_cookies.append({
                    'name': name,
                    'value': value,
                    'domain': '.people.com.cn',
                    'path': '/',
                })

        self._context = self._create_context(pw_cookies)
        self._page = self._context.new_page()
        self._page.set_default_timeout(30000)

        self._warmup()
        logging.info("Playwright 浏览器启动成功（stealth 模式）")

    def _warmup(self):
        """预热浏览器（模拟真实用户的浏览路径）"""
        try:
            # 第一步：访问人民网首页
            self._page.goto('https://paper.people.com.cn/',
                            wait_until='domcontentloaded', timeout=20000)
            time.sleep(random.uniform(2, 4))

            # 模拟真实的鼠标移动
            self._simulate_human_behavior()

            # 第二步：进入电子版
            self._page.goto('https://paper.people.com.cn/rmrb/pc/',
                            wait_until='domcontentloaded', timeout=20000)
            time.sleep(random.uniform(2, 4))

            self._simulate_human_behavior()

        except Exception as e:
            logging.warning(f"浏览器预热失败: {e}")

    def _simulate_human_behavior(self):
        """模拟真实人类行为（鼠标移动 + 滚动 + 停顿）"""
        try:
            viewport = self._page.viewport_size
            if not viewport:
                return

            w, h = viewport['width'], viewport['height']

            # 随机鼠标移动 2-4 次
            for _ in range(random.randint(2, 4)):
                x = random.randint(100, w - 100)
                y = random.randint(100, h - 100)
                self._page.mouse.move(x, y)
                time.sleep(random.uniform(0.1, 0.4))

            # 随机小幅滚动
            scroll_y = random.randint(100, 400)
            self._page.mouse.wheel(0, scroll_y)
            time.sleep(random.uniform(0.3, 0.8))

        except Exception:
            pass  # 行为模拟失败不影响主流程

    def get_page(self, url: str, shared_cookies: Optional[dict] = None) -> Optional[str]:
        """获取页面内容（Playwright stealth），含自动恢复与 context 轮换"""
        self._ensure_browser(shared_cookies)

        # 健康检查
        if not self._is_alive():
            self._restart_browser()

        # context 轮换检查
        if self.request_count >= self._rotate_threshold:
            self._rotate_context()

        retries = 0
        while retries < self.max_retries:
            try:
                self.request_count += 1

                # 每 10 次请求长休息（模拟人类的阅读间隔）
                if self.request_count > 1 and self.request_count % 10 == 0:
                    rest_time = random.uniform(20, 40)
                    logging.info(f"已请求 {self.request_count} 次，休息 {rest_time:.0f} 秒...")
                    time.sleep(rest_time)

                # 请求间隔（带抖动的随机延迟）
                base_interval = random.uniform(*self.request_interval)
                jitter = random.uniform(-2, 3)
                sleep_time = max(5, base_interval + jitter)
                logging.info(f"等待 {sleep_time:.0f}s 后请求: {url.split('/')[-1]}")
                time.sleep(sleep_time)

                # 导航到目标页面
                self._page.goto(url, wait_until='domcontentloaded', timeout=30000)
                time.sleep(random.uniform(1.5, 3))

                # 模拟人类交互
                self._simulate_human_behavior()

                # 额外等待页面 JS 渲染
                time.sleep(random.uniform(0.5, 1.5))

                page_source = self._page.content()

                if self._is_blocked(page_source):
                    retries += 1
                    wait_time = 60 * retries + random.uniform(0, 30)
                    logging.warning(f"检测到反爬虫拦截，等待 {wait_time:.0f}s 后重试...")
                    time.sleep(wait_time)

                    # 被拦截后轮换 context
                    self._rotate_context()
                    continue

                return page_source

            except Exception as e:
                retries += 1
                extra_delay = retries * 15 + random.uniform(0, 10)
                logging.warning(f"请求失败，等待 {extra_delay:.0f}s 后第 {retries} 次重试: {e}")
                time.sleep(extra_delay)

                # 如果浏览器连接已断，尝试重启
                if not self._is_alive():
                    self._restart_browser()

                if retries >= self.max_retries:
                    logging.error(f"请求 {url} 失败，已达到最大重试次数")
                    return None

        return None

    def _is_blocked(self, text: str) -> bool:
        """检测是否被反爬拦截"""
        if not text or len(text) < 500:
            return True
        first_block = text[:1000]
        if '403' in first_block and 'Forbidden' in first_block:
            return True
        if '验证' in first_block and '安全' in first_block:
            return True
        if 'captcha' in first_block.lower():
            return True
        if 'access denied' in first_block.lower():
            return True
        return False

    def _close_internal(self):
        """内部关闭资源（不做日志提示）"""
        try:
            if self._page and not self._page.is_closed():
                self._page.close()
        except Exception:
            pass
        try:
            if self._context:
                self._context.close()
        except Exception:
            pass
        try:
            if self._browser:
                self._browser.close()
        except Exception:
            pass
        try:
            if self._playwright:
                self._playwright.stop()
        except Exception:
            pass
        self._page = None
        self._context = None
        self._browser = None
        self._playwright = None

    def close(self):
        """关闭浏览器"""
        self._close_internal()
        logging.info("Playwright 浏览器已关闭")


class PeopleDailyCrawler:
    """人民日报爬虫类 - 双模式：requests.Session + Playwright stealth

    目录页使用 requests.Session 串行抓取（简单可靠，无 event loop 问题），
    文章页使用 Playwright stealth 模式抓取（绕过反爬）。
    Cookie 在两个通道间共享。
    """

    def __init__(self, config: Config):
        self.config = config
        self.url_generator = URLGenerator()
        # requests 同步抓取目录页
        self.requests_fetcher = RequestsFetcher(config)
        # Playwright 延迟初始化，仅在下载文章时启动
        self.playwright_browser = PlaywrightBrowser(config)

    def get_all_nodes(self, date: datetime) -> List[str]:
        """获取指定日期的所有版面节点ID"""
        url = self.url_generator.generate_url(date, "01")
        page_source = self.requests_fetcher.get_page(url)
        if not page_source:
            return ["01"]

        node_pattern = re.compile(r'node_(\d+)\.html')
        matches = node_pattern.findall(page_source)

        node_ids = sorted(list(set(matches)))
        if not node_ids:
            return ["01"]

        logging.info(f"找到 {len(node_ids)} 个版面")
        return node_ids

    def crawl_all_directories(self, date: datetime) -> List[Tuple[str, str]]:
        """抓取所有版面的目录页（使用 requests 串行抓取）

        相比 aiohttp 异步方式，requests 串行虽然慢一些，
        但完全避免了 event loop 管理问题，且目录页数量有限（通常 8-24 个），
        加上短间隔（1.5-4s），总耗时可控。
        """
        node_ids = self.get_all_nodes(date)
        results = []

        logging.info(f"开始抓取 {len(node_ids)} 个目录页...")

        for node_id in node_ids:
            url = self.url_generator.generate_url(date, node_id)
            page_source = self.requests_fetcher.get_page(url)
            if page_source:
                results.append((url, page_source))
            else:
                logging.warning(f"抓取版面 {node_id} 失败")

        logging.info(f"目录页抓取完成：成功 {len(results)}/{len(node_ids)} 个")
        return results

    def crawl_article(self, article_url: str) -> Optional[str]:
        """抓取文章页（使用 Playwright stealth 绕过反爬）

        自动共享 requests session 的 cookie 到 Playwright，
        维持一致的会话身份。
        """
        shared_cookies = self.requests_fetcher.get_cookies_dict()
        return self.playwright_browser.get_page(article_url, shared_cookies)

    def close(self):
        """关闭爬虫"""
        self.playwright_browser.close()
