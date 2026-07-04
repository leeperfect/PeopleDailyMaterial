# 修复 render_wechat_html.py 的 CSS 变量解析问题

## 摘要

写作工作流的 7 个步骤（AI 写稿 → humanizer-zh 润色 → getnote 推送 → APP 手动润色 → getnote 拉回 → 排版预览 → 微信草稿箱同步）已基本实现完成。唯一待办是修复 `render_wechat_html.py` 渲染时 CSS 变量丢失的问题：premailer 的 cssutils 引擎不支持 CSS 变量（`:root` 自定义属性和 `var()` 函数），导致产出的 HTML 缺少 color / line-height / text-indent 等核心样式。

本次修复只改 `render_wechat_html.py` 一个文件，`publish_wechat_draft.py` 通过 import 复用渲染函数会自动受益，CSS 模板保持变量形式不动（符合项目"样式不写死绝对值"的解耦规范）。

## 现状分析

### 问题根因

`scripts/assets/wechat_article.css` 使用 `:root` 定义了 9 个 CSS 变量（`--line-height`、`--text-color`、`--accent-color`、`--quote-bg`、`--quote-border`、`--indent`、`--font-size`、`--code-bg`），所有选择器通过 `var(--xxx)` 引用。这种写法符合项目"使用全局 CSS 变量，不写死绝对值"的规范。

但 `render_wechat_html.py` 的 `render_markdown_to_html` 函数把 CSS 原样交给 premailer 处理。premailer 底层的 cssutils 是 CSS 2.1 解析器，不认识 `:root` 自定义属性和 `var()` 函数，会把这些当作无效值丢弃。实测渲染 33-【R】文章时产生大量 `CSSUTILS WARNING/ERROR`（如 "Unknown Property name. --line-height"、"Invalid value for CSS Level 2.1 property: var(--font-size)"），产出的 HTML 虽然有 30441 字符，但内联 style 属性缺少关键样式值。

### 影响范围

- `render_wechat_html.py`（A 层步骤 6 排版预览）：产出的预览 HTML 样式缺失
- `publish_wechat_draft.py`（B 层全自动方案）：第 42 行 `from render_wechat_html import ... render_markdown_to_html` 复用该函数，推送到草稿箱的 HTML 同样会样式缺失

### 当前文件状态

`render_wechat_html.py`（180 行）：
- import 部分（17-20 行）：`argparse`、`os`、`sys`、`typing.Optional`，缺少 `re` 和 `logging`
- `render_markdown_to_html`（42-76 行）：读 CSS 后直接拼接 `<section><style>{css_text}</style>...` 交给 `transform()`，无变量解析
- 无 cssutils 日志抑制

`wechat_article.css`（152 行）：`:root` 块（11-20 行）+ 所有选择器用 `var()` 引用，结构清晰，无需修改。

## 修改方案

### 修改文件：`scripts/render_wechat_html.py`

#### 改动 1：补充 import（第 17-20 行）

在现有 import 块加入 `logging` 和 `re`：

```python
# 原：
import argparse
import os
import sys
from typing import Optional

# 改为：
import argparse
import logging
import os
import re
import sys
from typing import Optional
```

**为什么**：`re` 用于解析 `:root` 变量定义和替换 `var()`；`logging` 用于抑制 cssutils 的警告日志，避免渲染输出被大量 CSSUTILS WARNING 刷屏。

#### 改动 2：新增 `resolve_css_variables` 函数（插入在 `render_markdown_to_html` 之前，即第 41 行附近）

```python
def resolve_css_variables(css_text: str) -> str:
    """把 CSS 变量定义解析并替换所有 var() 引用为直接值。

    Why: premailer 的 cssutils 引擎是 CSS 2.1 解析器，不认识 :root 自定义属性
         和 var() 函数，会把这些当作无效值丢弃，导致 color/line-height/
         text-indent 等核心样式全部丢失。必须在交给 premailer 前把变量
         替换为直接值，并移除 :root 块。
    """
    # 1. 提取 :root 变量定义
    root_match = re.search(r':root\s*\{([^}]+)\}', css_text)
    if not root_match:
        return css_text

    variables = {}
    for line in root_match.group(1).split('\n'):
        line = line.strip()
        if line.startswith('--') and ':' in line:
            name, _, value = line.partition(':')
            variables[name.strip()] = value.rstrip(';').strip()

    # 2. 替换所有 var(--xxx) 和 var(--xxx, fallback) 引用
    #    多轮替换以处理 var() 嵌套引用（变量值本身又引用另一变量）
    def replace_var(match):
        name = match.group(1).strip()
        fallback = match.group(2)
        return variables.get(name, fallback.strip() if fallback else match.group(0))

    var_pattern = re.compile(r'var\((--[\w-]+)\s*(?:,\s*([^)]+))?\)')
    for _ in range(3):  # 最多 3 轮，足够处理当前模板的嵌套深度
        new_css = var_pattern.sub(replace_var, css_text)
        if new_css == css_text:
            break
        css_text = new_css

    # 3. 移除 :root 块（避免 cssutils 报 Unknown Property 警告）
    css_text = re.sub(r':root\s*\{[^}]+\}', '', css_text)
    return css_text
```

**为什么这么设计**：
- 用正则而非 CSS 解析库：cssutils 本身就不支持变量，用正则在预处理阶段解决最轻量可靠。
- 支持带 fallback 的 `var(--xxx, default)` 形式：当前模板没用，但符合项目"考虑代码健壮性"规范，未来扩展 CSS 不会踩坑。
- 多轮替换（最多 3 轮）：处理变量值本身又引用另一变量的嵌套情况，当前模板无嵌套但留出余量。
- 移除 `:root` 块：即使变量已替换，`:root` 里的 `--xxx: value` 声明仍会被 cssutils 当作 Unknown Property 报警告，必须清掉。

#### 改动 3：在 `render_markdown_to_html` 内调用解析 + 抑制日志（第 63-75 行附近）

在"读 CSS 模板"之后、"用 section 包裹"之前，插入变量解析；并在函数开头 import premailer 时抑制 cssutils 日志：

```python
# 在 try import 块内，import premailer 后追加日志抑制：
    try:
        import markdown
        from premailer import transform
        # 抑制 cssutils 对 CSS 变量等不识别语法的 WARNING/ERROR 日志
        logging.getLogger('cssutils').setLevel(logging.CRITICAL)
    except ImportError as e:
        ...

# 读 CSS 模板后追加一行变量解析：
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            css_text = f.read()
    except FileNotFoundError:
        print(f"CSS 模板不存在: {css_path}")
        sys.exit(1)

    # 在交给 premailer 前把 CSS 变量解析为直接值（premailer 不支持 var()）
    css_text = resolve_css_variables(css_text)

    # 用 <section> 包裹 ...
    full_html = f"<section><style>{css_text}</style>{body_html}</section>"
```

**为什么**：日志抑制放在 import 成功后立即执行，确保后续 `transform()` 调用时 cssutils 已静默；变量解析放在读 CSS 之后、拼接 HTML 之前，保证交给 premailer 的 CSS 已是纯直接值。

### 不修改的文件

- `scripts/assets/wechat_article.css`：保持 `:root` + `var()` 形式，符合项目"样式不写死绝对值"的解耦规范。变量解析是渲染层的职责，不应要求 CSS 模板退化为写死值。
- `scripts/publish_wechat_draft.py`：第 42 行通过 `from render_wechat_html import render_markdown_to_html` 复用，修复后自动受益，无需改动。
- `config.json` / `config.json.example`：渲染相关配置已就绪，无需调整。

## 假设与决策

1. **假设**：当前 `wechat_article.css` 的 `var()` 都是简单引用形式（已核实，9 处均为 `var(--xxx)`，无 fallback、无嵌套）。修复方案仍支持 fallback 和嵌套，属前瞻性健壮性设计。
2. **决策**：用正则预处理而非更换 premailer 的 CSS 解析后端。premailer 的 cssutils 不支持变量是其已知限制，正则预处理是最小侵入的解法，无需引入新依赖。
3. **决策**：日志抑制只针对 `cssutils` logger，不影响项目其他日志输出（`modules/utils.py` 的 `setup_logger` 用的是 root logger）。
4. **环境注意**：运行渲染命令时需用 `env -u PYTHONHOME -u PYTHONPATH .venv/bin/python` 前缀清除 TRAE 注入的环境变量，否则 .venv 的 Python 3.14 会因找错标准库路径而报 "Failed to import encodings module"。这是已验证的环境约束。

## 验证步骤

1. **语法检查**：`env -u PYTHONHOME -u PYTHONPATH .venv/bin/python -m py_compile scripts/render_wechat_html.py`，确认无语法错误。

2. **重新渲染 33-【R】文章**：
   ```bash
   env -u PYTHONHOME -u PYTHONPATH .venv/bin/python scripts/render_wechat_html.py "data/articles/人民日报系列/33-【R】人民日报讲服务业高质量发展：从"卖产品"到"卖体验、卖品牌、卖信任".md"
   ```
   预期：无 CSSUTILS WARNING/ERROR 输出，"渲染完成" + HTML 大小正常。

3. **检查产出 HTML 的内联样式**：打开 `data/exports/wechat_html/33-【R】人民日报讲服务业高质量发展：从"卖产品"到"卖体验、卖品牌、卖信任".html`，确认：
   - `<section>` 标签含 `style="font-size: 16px; color: #333; line-height: 1.75"`（变量已替换为直接值）
   - `<p>` 标签含 `style="... line-height: 1.75; text-align: justify; text-indent: 2em; ... color: #333"`
   - `<h1>` / `<h2>` 标签含 `color: #c039b`（accent-color 已替换）
   - `<blockquote>` 含 `background: #f7f7f7; border-left: 4px solid #c0392b`
   - 不再出现 `var(--xxx)` 字样
   - 不再出现 `:root` 块

4. **TRAE 内预览验证**：渲染加 `--open` 参数，用 OpenPreview 打开产出的 `file://` 地址，确认浏览器中排版正常（行高、缩进、颜色、引用块样式均生效）。

5. **publish_wechat_draft.py 联动确认**：`env -u PYTHONHOME -u PYTHONPATH .venv/bin/python -m py_compile scripts/publish_wechat_draft.py`，确认 import 链路未被破坏。
