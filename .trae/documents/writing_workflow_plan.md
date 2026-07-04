# 写作工作流实现方案

## 一、摘要

构建一条从「AI 写作 → humanizer-zh 润色 → 得到大脑二次润色 → doocs/md 排版 → 微信草稿箱」的完整工作流。核心结论：

- **排版预览能否在 TRAE 内直接完成**：能，但属于「半自动」。由 AI 在对话内启动 `md-cli` 本地服务并用 `OpenPreview` 打开预览，用户无需自己开终端或浏览器。**纯对话内渲染微信图文不可行**——微信排版必须把 CSS 内联到每个标签的 `style` 属性，对话流内的 HTML 容器无法承载这种样式，必须依赖浏览器渲染引擎。
- **草稿箱直接同步**：doocs/md 本身只「复制 HTML 到剪贴板」，不调微信 API。要实现「不手动粘贴」，需自定义脚本调用微信 `draft/add` 接口（需公众号 AppID/AppSecret + IP 白名单）。
- 方案分两层：**A 层（半自动，推荐日常）** 预览在 TRAE 内完成、草稿箱手动粘贴；**B 层（全自动增强，可选）** 一条命令推到草稿箱。

## 二、现状分析

| 环节 | 工具 | 现状 | 是否在 TRAE 内可自动化 |
|---|---|---|---|
| 写作 | TRAE 对话 | 已有，文章落 `data/articles/人民日报系列/`（下一篇 `35`）或 `data/articles/热点系列/`（下一篇 `热点4`） | 全程对话内 |
| 第一轮润色 | humanizer-zh | TRAE 内置 skill，项目已用于 33 号文章，产出 `编号-【R】原标题.md` | 对话内完成 |
| 推送得到大脑 | getnote-cli | `npm i -g @getnote/cli`，**需得到大脑会员** | 命令行可脚本化 |
| APP 手动润色 | 得到大脑 APP | 手机端操作，不在项目内 | 人工步骤 |
| 拉回 | getnote-cli | `getnote note <id> --field content` | 命令行可脚本化 |
| 排版预览 | doocs/md | `npm i -g @doocs/md-cli`，`md-cli` 启动本地 8800 端口 Web 服务 | 半自动（启动服务 + OpenPreview） |
| 微信草稿箱 | 微信 `draft/add` API | 需 AppID/AppSecret 换 access_token，需配 IP 白名单 | 全自动需自定义脚本 |

**命名约定**：润色稿 `编号-【R】原标题.md`，与原稿并存于同目录。`【R】` 标记值取自 config，不硬编码。31-r、32-r 是历史遗留写法，今后统一用 `【R】`。

## 三、工作流总览（7 步）

```text
1. AI 写文章          → 对话内生成原始稿 .md
2. humanizer-zh 润色   → 对话内润色，产出 编号-【R】原标题.md
3. getnote 推送大脑    → getnote_sync.py push，推送【R】稿，记 note_id
4. APP 手动润色        → 老师手机端二次润色
5. getnote 拉回        → getnote_sync.py pull，覆盖【R】稿正文（先备份）
6. doocs/md 排版预览   → render_wechat_html.py 产 HTML + OpenPreview / preview_wechat.py 启动 md-cli
7. 微信草稿箱          → A层：复制HTML粘贴后台 / B层：publish_wechat_draft.py 调 API
```

## 四、核心技术判断（回答用户疑问）

### 4.1 排版预览能否在 TRAE 内完成？

**能，半自动。** 两条路径：

- **路径一（推荐，本地渲染 HTML）**：`render_wechat_html.py` 把 Markdown 渲染成微信内联样式 HTML 文件 → TRAE 对该 HTML 文件用 `OpenPreview` 打开，所见即所得。全程在 TRAE 内，不需开终端或浏览器。样式由 `scripts/assets/wechat_article.css` 控制（CSS 变量，不写死绝对值）。
- **路径二（交互调样式，偶尔用）**：AI 用 `RunCommand`（非阻塞）启动 `md-cli` → 打印 `http://127.0.0.1:8800/md/` → 用 `OpenPreview` 打开该 URL，用户在 doocs/md 网页内粘贴 Markdown、调主题、一键复制 HTML。

**为何不能纯对话内渲染**：微信编辑器会剥离 `<style>` 块和 class 选择器，doocs/md 的核心价值就是把 CSS 内联到每个标签的 `style` 属性。对话流内的 HTML 容器（如 inline widget）无法承载这种内联样式渲染，必须用浏览器引擎。所以「在 TRAE 内」=「AI 自动启动服务 + OpenPreview 预览」，不是「不启动任何服务」。

### 4.2 草稿箱能否不手动粘贴？

**A 层不能，B 层能。** doocs/md 的「一键排版」是复制 HTML 到剪贴板，不调微信 API。要不手动粘贴，需 B 层脚本调微信 `draft/add`：
- 端点：`POST https://api.weixin.qq.com/cgi-bin/draft/add?access_token={token}`
- token：`GET https://api.weixin.qq.com/cgi-bin/token?grant_type=client_ccredential&appid={appid}&secret={secret}`
- token 有效期 2 小时、日限 2000 次，需缓存
- **前提**：公众号后台「设置-基本配置-IP白名单」加入本机出口公网 IP，否则报 errcode 40164

## 五、配置步骤（先做）

### 5.1 config.json 追加配置段

在现有 `/Users/pf.macbookpro/PeopleDailyMaterial/config.json`（已被 gitignore）追加：

```json
{
  "wechat": {
    "app_id": "你的公众号AppID",
    "app_secret": "你的公众号AppSecret",
    "ip_whitelist_tip": "需在公众号后台IP白名单加入本机出口公网IP"
  },
  "getnote": {
    "config_path": "~/.getnote/config.json",
    "push_cmd_template": "getnote save {content} --title {title} --tag 公众号润色",
    "pull_cmd_template": "getnote note {note_id} --field content",
    "list_cmd": "getnote notes -o json",
    "title_prefix": "人民日报素材-"
  },
  "writing_workflow": {
    "articles_base_dir": "data/articles",
    "series_dirs": {
      "people_daily": "人民日报系列",
      "hotspot": "热点系列"
    },
    "polished_marker": "【R】",
    "manifest_path": "data/exports/getnote_article_map.json",
    "token_cache_path": "data/exports/wechat_token_cache.json",
    "render": {
      "css_path": "scripts/assets/wechat_article.css",
      "html_output_dir": "data/exports/wechat_html"
    },
    "doocs": {
      "start_cmd": "md-cli",
      "default_port": 8800,
      "preview_url_template": "http://127.0.0.1:{port}/md/"
    }
  }
}
```

同步在 `config.json.example` 追加同结构占位（值替换为 `YOUR_WECHAT_APPID` 等）。**命令模板放 config 是本方案最关键的解耦决策**：getnote/doocs 命令语法若随版本变更，只改配置不改代码。

### 5.2 .gitignore 追加

```gitignore
# 写作工作流：微信 access_token 缓存（临时凭证，敏感，不入库）
data/exports/wechat_token_cache.json
```

### 5.3 外部工具凭证（均不进项目目录）

- **getnote-cli**：`npm i -g @getnote/cli` → `getnote auth login`（浏览器 OAuth 授权）→ 凭证落 `~/.getnote/config.json`（全局，天然不进 Git）。**需得到大脑会员**，未开通会报 `OpenAPI 仅对会员开放`。
- **doocs/md**：`npm i -g @doocs/md-cli`，无需凭证。
- **humanizer-zh**：TRAE 内置 skill，无需安装。
- **微信**：公众号后台取 AppID/AppSecret 填入 `config.json`，并把本机出口公网 IP 加入 IP 白名单。

### 5.4 Python 依赖（安装到现有 .venv）

项目无 requirements 文件，新增脚本依赖在文档说明，安装到现有 `.venv`（Python 3.14）：

```bash
.venv/bin/pip install markdown premailer requests
```

- `markdown`：md→html 解析
- `premailer`：把 `<style>` 块转为内联 style（微信会剥离 class/style 标签，必须内联）
- `requests`：调微信 API（若项目已有 HTTP 客户端则复用）

## 六、文件清单与职责（解耦设计）

| 文件路径 | 职责 | 类型 |
|---|---|---|
| `scripts/getnote_sync.py` | 封装 getnote-cli 推送/拉回，管理 note_id 映射 | Python 脚本 |
| `scripts/render_wechat_html.py` | Markdown → 微信内联样式 HTML（剥离 frontmatter） | Python 脚本 |
| `scripts/publish_wechat_draft.py` | 微信草稿箱 API（access_token + draft/add） | Python 脚本 |
| `scripts/preview_wechat.py` | 半自动预览辅助：启动 doocs/md 或打印本地 HTML 路径 | Python 脚本 |
| `scripts/assets/wechat_article.css` | 微信排版 CSS 变量模板（行高1.75/两端对齐/首行缩进） | 样式资产 |
| `docs/writing-workflow.md` | 工作流说明、命令清单、配置步骤、故障排查 | 文档 |
| `config.json`（追加段） | wechat / getnote / writing_workflow 配置 | 配置（已 gitignore） |
| `config.json.example`（追加段） | 同结构占位示例 | 配置模板 |
| `.gitignore`（追加） | 屏蔽 token 缓存等敏感产物 | 规则 |

设计要点：外部 CLI 的命令模板放 config.json，脚本只负责组装参数和文件读写。

## 七、A 层：半自动方案（推荐日常）

以编号 35 为例。

**步骤 1-2（对话内完成）**

TRAE 对话内：AI 生成原始稿 `35-人民日报讲XXX.md` → 调 humanizer-zh 润色 → 写入 `35-【R】人民日报讲XXX.md`（保留 frontmatter，正文替换）。

**步骤 3 推送大脑**

```bash
python3 scripts/getnote_sync.py push "data/articles/人民日报系列/35-【R】人民日报讲XXX.md"
```

脚本读润色稿 → 剥离 frontmatter 取正文 → 从文件名提取编号+标题作为笔记标题 → 调 `getnote save "正文" --title "标题" --tag 公众号润色` → 把返回的 note_id 写入 `data/exports/getnote_article_map.json`。

**步骤 4 手机 APP 手动润色**

老师在得到大脑 APP 内对这条笔记二次润色。

**步骤 5 拉回**

```bash
python3 scripts/getnote_sync.py pull "data/articles/人民日报系列/35-【R】人民日报讲XXX.md"
```

脚本查 manifest 得 note_id → 调 `getnote note {note_id} --field content` → 用拉回内容覆盖 `35-【R】` 稿正文（保留 frontmatter，原正文先备份到 `data/exports/wechat_html/35-【R】XXX.bak.md`）。

**步骤 6 排版预览（二选一）**

方式一（本地渲染预览，日常推荐）：
```bash
python3 scripts/render_wechat_html.py "data/articles/人民日报系列/35-【R】人民日报讲XXX.md"
# 产出 data/exports/wechat_html/35-【R】XXX.html，TRAE 内 OpenPreview 所见即所得
```

方式二（doocs/md 交互调样式，偶尔用）：
```bash
python3 scripts/preview_wechat.py --doocs
# 以非阻塞启动 md-cli（8800），打印 http://127.0.0.1:8800/md/ 供 OpenPreview
# 用户在 doocs/md 网页内粘贴 markdown，一键复制 HTML
```

**步骤 7 微信草稿箱（手动）**

打开方式一产出的 HTML 文件，全选复制 → 粘贴到微信公众号后台编辑器。

## 八、B 层：全自动增强方案

一条命令把润色稿推到微信草稿箱：

```bash
python3 scripts/publish_wechat_draft.py "data/articles/人民日报系列/35-【R】人民日报讲XXX.md" \
  --title "人民日报讲XXX" --pull-from-getnote --dry-run
```

`--dry-run` 先预览 payload（标题、HTML 长度、封面 media_id）不实际提交；去掉 `--dry-run` 正式推草稿箱。`--pull-from-getnote` 表示先拉回 getnote 最新内容再渲染。

内部链路：`publish_wechat_draft.py` 调 `render_wechat_html.py` 的渲染函数（同目录 import 复用）→ 取 access_token（命中缓存则用，过期则刷新）→ 组装 draft/add payload → POST 提交。各脚本仍可单独运行，保证解耦。

## 九、各脚本设计要点

所有脚本遵循现有 `sync_to_notion.py` 风格：`PROJECT_ROOT` 定位、`from modules.utils import Config, setup_logger`、argparse、try/except、snake_case、函数级注释解释 Why。

### 9.1 `scripts/getnote_sync.py`

核心函数：
- `derive_polished_path(article_path)`：由原始稿路径推断【R】润色稿路径。正则 `^(\d+|热点\d+)-` 匹配编号前缀，在其后插入 `【R】`。
- `load_manifest()` / `save_manifest()`：读写 `data/exports/getnote_article_map.json`，原子写入（先写 .tmp 再 rename）防中途崩溃损坏。
- `push_to_getnote(article_path, config)`：推送润色稿返回 note_id。用 subprocess 调 getnote-cli（args 数组传递正文，绕过 shell 长度限制）。异常：FileNotFoundError(未装CLI)、CalledProcessError(推送失败)、超时。重试：网络/CLI 失败重试 3 次，指数退避 1/2/4 秒。
- `pull_from_getnote(article_path, config)`：拉回覆盖【R】稿正文，保留 frontmatter，原正文先备份。

子命令：`push <file>`、`pull <file>`、`list`（查看 manifest）。

### 9.2 `scripts/render_wechat_html.py`

核心函数：
- `strip_frontmatter(markdown_text)`：剥离 YAML frontmatter，只渲染正文（frontmatter 是项目索引用，微信不需要）。
- `render_markdown_to_html(md_text, css_path)`：markdown 解析 + premailer 内联样式。流程：`markdown.markdown(extensions=['extra','nl2br'])` → 包 `<style>` → `premailer.transform`。
- `render_article_file(article_path, config)`：主入口，返回产出 html 路径。

CSS 模板 `scripts/assets/wechat_article.css`（CSS 变量，不写死绝对值）：

```css
:root {
  --line-height: 1.75;
  --text-color: #333;
  --accent-color: #c0392b;
  --quote-bg: #f7f7f7;
  --indent: 2em;
}
section p { line-height: var(--line-height); text-align: justify; text-indent: var(--indent); }
section blockquote { background: var(--quote-bg); border-left: 4px solid var(--accent-color); padding: 10px 14px; }
section h2 { color: var(--accent-color); border-bottom: 1px solid #eee; }
```

### 9.3 `scripts/publish_wechat_draft.py`

核心函数：
- `get_access_token(config)`：取 token，命中缓存且未过期直接返回，否则刷新。缓存 `data/exports/wechat_token_cache.json`。异常：40164(IP白名单)、40001(无效token)、网络超时。
- `upload_thumb_media(config, image_path)`：上传封面图得 thumb_media_id（可选）。
- `create_draft(html, title, config, thumb_media_id)`：POST draft/add，返回 media_id。token 过期自动刷新重试 1 次。
- `publish(article_path, config, pull_first, dry_run)`：编排，可选拉回 getnote → render → 取 token → draft/add。

### 9.4 `scripts/preview_wechat.py`

- `start_doocs(config)`：非阻塞启动 md-cli，返回端口。
- `open_local_html(html_path)`：打印本地 html 路径供 TRAE OpenPreview。

子命令：`--doocs`、`--html <path>`。轻量辅助脚本。

## 十、命名约定处理

`derive_polished_path` 统一处理：

| 输入 | 推断输出 |
|---|---|
| `35-人民日报讲XXX.md` | `35-【R】人民日报讲XXX.md` |
| `35-【R】人民日报讲XXX.md` | 原样返回 |
| `热点4-官媒视角看XXX.md` | `热点4-【R】官媒视角看XXX.md` |

## 十一、风险与边界

| 风险 | 应对 |
|---|---|
| getnote-cli 命令语法随版本变 | 命令模板放 config.json，脚本读配置组装 |
| 微信 access_token 泄露 | token 缓存单独 gitignore；config.json 已 gitignore |
| 拉回覆盖丢失人工润色 | pull 前自动备份正文到 `.bak.md` |
| premailer 依赖 lxml 在 macOS 安装偶发失败 | 文档备注 `xcode-select --install` 前置；备选 `css_inline` 包（预编译 wheel） |
| doocs/md 8800 端口被占 | md-cli 自动换端口；脚本解析启动日志取实际端口 |
| 微信 IP 白名单（家用动态 IP） | 全自动层不适合频繁变 IP 环境；动态 IP 时退回 A 层手动粘贴 |
| getnote 长文章通过命令行传递 | subprocess 用 args 数组传递（非 shell 字符串），绕过 ARG_MAX 限制 |

## 十二、落地顺序

1. 配置层：追加 `config.json` / `config.json.example` / `.gitignore`。
2. `render_wechat_html.py` + CSS 模板（A 层步骤 6 立即可用，价值最高、风险最低）。
3. `getnote_sync.py`（步骤 3/5，依赖外部 CLI 但逻辑独立）。
4. `preview_wechat.py`（轻量辅助）。
5. `publish_wechat_draft.py`（B 层，依赖微信凭证与 IP 白名单，最后做）。
6. 全程配套 `docs/writing-workflow.md`，每完成一个脚本补对应章节。

每步落地后用 `--dry-run` 或小样验证，再进入下一步。

## 十三、验证步骤

- `render_wechat_html.py`：对 33 号【R】稿渲染，OpenPreview 打开 HTML，与 doocs/md 在线版对比样式。
- `getnote_sync.py push`：推送 33 号稿，确认得到大脑 APP 出现该笔记，manifest 写入 note_id。
- `getnote_sync.py pull`：在 APP 内改动一个字，拉回确认本地文件更新且备份存在。
- `publish_wechat_draft.py --dry-run`：确认 payload 正确（标题、HTML 长度）。
- `publish_wechat_draft.py`（正式）：确认公众号后台草稿箱出现新草稿。

## 十四、假设与决策

- 假设用户有得到大脑会员（getnote-cli 必需）；若无，步骤 3-5 退化为手动复制粘贴到得到大脑。
- 假设用户有公众号 AppID/AppSecret 且能配 IP 白名单（B 层必需）；若无，B 层不可用，仅用 A 层。
- 决策：A 层为默认推荐，B 层为可选增强，不强依赖。
- 决策：外部 CLI 命令模板放 config.json，不写死脚本，保证工具版本变更只改配置。
- 决策：humanizer-zh 作为对话内 skill 运行，不产生独立脚本，由对话直接写入【R】文件。
