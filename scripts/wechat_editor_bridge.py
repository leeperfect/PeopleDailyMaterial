#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""承接 doocs/md，提供本地双平台配图与预览工作台。"""

from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from modules.writing_workflow import (
    article_state,
    atomic_write_text,
    body_hash,
    join_frontmatter,
    load_public_config,
    load_state,
    project_path,
    save_snapshot,
    save_state,
    split_frontmatter,
    structural_issues,
    workflow_id,
)
from modules.figure_workflow import (
    add_manual_figure,
    apply_plan,
    article_headings,
    canonical_markdown,
    confirm_figures,
    editor_markdown,
    ensure_manual_manifest,
    effective_plan,
    figure_by_id,
    invalidate_article_confirmation,
    load_manifest,
    reset_platform_override,
    sync_usage,
)
from render_wechat_html import render_article, save_layout
from render_toutiao_html import render_toutiao


class EditorWorkflow:
    def __init__(self, article: str, port: int) -> None:
        self.config = load_public_config()
        self.article_path = project_path(article).resolve()
        if not self.article_path.exists():
            raise RuntimeError(f"文章不存在：{self.article_path}")
        self.workflow_id = workflow_id(self.article_path)
        self.port = port
        self.last_result: dict[str, object] = {}
        self.restore_last_result()

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def restore_last_result(self) -> None:
        state = load_state(self.config)
        entry = article_state(state, self.article_path)
        if not entry or not entry.get("layout_saved_at"):
            return
        rendered = render_article(str(self.article_path))
        self.last_result = {
            "saved": True,
            "content_changed": bool(entry.get("editor_content_changed")),
            "content_synced": bool(entry.get("editor_content_synced")),
            "sync_blocked": bool(entry.get("editor_sync_blocked")),
            "sync_issues": list(entry.get("editor_sync_issues") or []),
            "candidate_path": str(entry.get("editor_candidate") or ""),
            "layout": dict(entry.get("wechat_layout") or {}),
            "preview_path": rendered["preview_path"],
            "saved_at": entry["layout_saved_at"],
            "media_id": entry.get("wechat_draft_media_id"),
        }

    def save_handoff(self, payload: dict[str, object]) -> dict[str, object]:
        if str(payload.get("workflow_id") or "") != self.workflow_id:
            raise RuntimeError("文章工作流标识不匹配，已停止保存")

        source = self.article_path.read_text(encoding="utf-8")
        frontmatter, body, metadata = split_frontmatter(source)
        editor_markdown = canonical_markdown(
            self.article_path,
            str(payload.get("markdown") or "").strip(),
        )
        if not editor_markdown:
            raise RuntimeError("编辑器正文为空，已停止保存")

        layout_payload = payload.get("layout")
        if not isinstance(layout_payload, dict):
            raise RuntimeError("编辑器没有返回排版参数")

        allowed = set(self.config["doocs"]["default_layout"])
        layout_updates = {
            key: value
            for key, value in layout_payload.items()
            if key in allowed
        }
        layout = save_layout(str(self.article_path), layout_updates)

        content_changed = editor_markdown.strip() != body.strip()
        content_synced = False
        sync_blocked = False
        sync_issues: list[str] = []
        candidate_path: Path | None = None
        before_sync_path: Path | None = None
        if content_changed:
            candidate_path = save_snapshot(
                self.article_path,
                metadata,
                "04-editor-candidate.md",
                join_frontmatter(frontmatter, editor_markdown),
            )
            sync_issues = structural_issues(body, editor_markdown)
            if sync_issues:
                sync_blocked = True
            else:
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
                before_sync_path = save_snapshot(
                    self.article_path,
                    metadata,
                    f"04-before-editor-sync-{timestamp}.md",
                    source,
                )
                atomic_write_text(
                    self.article_path,
                    join_frontmatter(frontmatter, editor_markdown),
                )
                content_synced = True

        if content_synced:
            try:
                invalidate_article_confirmation(self.article_path)
            except RuntimeError:
                # 尚未登记配图时，正文仍可正常保存。
                pass

        sync_usage(self.article_path, editor_markdown if content_synced else body)

        rendered = render_article(str(self.article_path))
        state = load_state(self.config)
        entry = article_state(state, self.article_path, create=True)
        assert entry is not None
        previous_status = str(entry.get("status") or "")
        next_status = previous_status or "figures_editing"
        if content_synced:
            next_status = "figures_editing"
        entry.update(
            {
                "status": (
                    "editor_sync_blocked" if sync_blocked else next_status
                ),
                "layout_saved_at": datetime.now().isoformat(timespec="seconds"),
                "editor_content_changed": content_changed,
                "editor_content_synced": content_synced,
                "editor_sync_blocked": sync_blocked,
                "editor_sync_issues": sync_issues,
                "editor_body_hash": body_hash(
                    editor_markdown if content_synced else body
                ),
                "editor_candidate": (
                    str(candidate_path.relative_to(PROJECT_ROOT))
                    if candidate_path
                    else None
                ),
                "before_editor_sync_snapshot": (
                    str(before_sync_path.relative_to(PROJECT_ROOT))
                    if before_sync_path
                    else None
                ),
            }
        )
        save_state(state, self.config)

        self.last_result = {
            "saved": True,
            "content_changed": content_changed,
            "content_synced": content_synced,
            "sync_blocked": sync_blocked,
            "sync_issues": sync_issues,
            "candidate_path": str(candidate_path) if candidate_path else "",
            "layout": layout,
            "preview_path": rendered["preview_path"],
            "saved_at": entry["layout_saved_at"],
        }
        return {
            **self.last_result,
            "next_url": "/pd-workflow/result",
        }

    def editor_body(self) -> str:
        source = self.article_path.read_text(encoding="utf-8")
        _, body, _ = split_frontmatter(source)
        return editor_markdown(self.article_path, body)

    def figure_data(self) -> dict[str, object]:
        _, manifest = ensure_manual_manifest(self.article_path)
        _, body, _ = split_frontmatter(self.article_path.read_text(encoding="utf-8"))
        return {
            "figures": manifest["figures"],
            "headings": article_headings(body),
            "plans": {
                "shared": list(manifest["plans"]["shared"].get("items") or []),
                "wechat": effective_plan(manifest, "wechat"),
                "toutiao": effective_plan(manifest, "toutiao"),
            },
            "inherited": {
                "wechat": manifest["plans"]["wechat"].get("items") is None,
                "toutiao": manifest["plans"]["toutiao"].get("items") is None,
            },
            "confirmation": manifest.get("confirmation") or {},
        }

    def upload_figure(self, payload: dict[str, object]) -> dict[str, object]:
        filename = str(payload.get("filename") or "").strip()
        encoded = str(payload.get("data_base64") or "")
        if not filename or not encoded:
            raise RuntimeError("没有收到可登记的图片")
        try:
            data = base64.b64decode(encoded, validate=True)
        except Exception as error:
            raise RuntimeError("图片传输数据无效") from error
        result = add_manual_figure(self.article_path, filename=filename, data=data)
        figure = result["figure"]
        if result["duplicate"]:
            message = f"“{figure['title']}”已经在候选图片中，无需重复添加。"
        else:
            message = f"已加入“{figure['title']}”，请选择插入位置并保存方案。"
        return {**result, "message": message}

    def apply_figures(self, payload: dict[str, object]) -> dict[str, object]:
        plan = payload.get("plan")
        if not isinstance(plan, list):
            raise RuntimeError("配图计划格式异常")
        platform = str(payload.get("platform") or "shared")
        result = apply_plan(self.article_path, plan, platform=platform)
        wechat = render_article(str(self.article_path))
        toutiao = render_toutiao(str(self.article_path))
        return {
            **result,
            "wechat_preview": "/pd-workflow/preview/wechat",
            "toutiao_preview": "/pd-workflow/preview/toutiao",
            "message": f"已保存{result['used_count']}张配图，两个平台预览均已刷新。",
        }

    def reset_figures(self, payload: dict[str, object]) -> dict[str, object]:
        platform = str(payload.get("platform") or "")
        result = reset_platform_override(self.article_path, platform)
        render_article(str(self.article_path))
        render_toutiao(str(self.article_path))
        return {**result, "message": "已恢复为共用配图方案。"}

    def confirm_figure_plan(self) -> dict[str, object]:
        # 只有两个正式预览都能生成时，才允许把人工确认写入状态。
        wechat = render_article(str(self.article_path))
        toutiao = render_toutiao(str(self.article_path))
        result = confirm_figures(self.article_path)
        return {
            **result,
            "wechat_preview": wechat["preview_path"],
            "toutiao_preview": toutiao["preview_path"],
            "message": "配图已人工确认，现在可以执行“同步双平台草稿”。",
        }

    def figure_asset(self, figure_id: str) -> Path:
        _, manifest = load_manifest(self.article_path)
        figure = figure_by_id(manifest, figure_id)
        path = project_path(str(figure["file"])).resolve()
        if not path.exists() or not path.is_file():
            raise RuntimeError(f"配图文件不存在：{path}")
        return path

    def figure_tray_html(self) -> str:
        data = self.figure_data()
        headings = data["headings"]
        assert isinstance(headings, list)
        options = "".join(
            f'<option value="{html.escape(str(item["value"]))}">{html.escape(str(item["label"]))}</option>'
            for item in headings
        )
        cards: list[str] = []
        for figure in data["figures"]:
            figure_id = str(figure["id"])
            cards.append(
                f"""<article class="figure" data-id="{html.escape(figure_id)}">
<img src="/pd-workflow/asset/{html.escape(figure_id)}" alt="{html.escape(str(figure.get('title') or figure_id))}">
<div class="body"><label class="pick"><input type="checkbox">用于正文</label>
<h2>{html.escape(str(figure.get('title') or figure_id))}</h2>
<p>{figure.get('width_px')}×{figure.get('height_px')}｜清晰度：{html.escape('正常' if figure.get('quality_status') != 'low_resolution_warning' else '建议换更清晰图片')}</p>
<select>{options}</select></div></article>"""
            )
        payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
        heading_list = "".join(
            f'<li data-heading="{html.escape(str(item["value"]))}"><strong>{html.escape(str(item["label"]))}</strong><span></span></li>'
            for item in headings
        )
        return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>双平台配图工作台</title>
<style>
body{{margin:0;background:#f3f4f6;color:#111827;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}
header{{position:sticky;top:0;z-index:10;background:#fffffff2;padding:14px 18px;border-bottom:1px solid #e5e7eb;backdrop-filter:blur(12px)}}
.top,.modes,.actions,.preview-tabs{{display:flex;gap:10px;align-items:center;flex-wrap:wrap}}.top h1{{font-size:23px;margin:0 12px 0 0}}header p{{margin:7px 0;color:#64748b}}
button{{border:0;border-radius:9px;padding:10px 15px;cursor:pointer;background:#e5e7eb;color:#111827}}button.primary{{background:#ff6a2a;color:white}}button.confirm{{background:#047857;color:white}}button.active{{background:#111827;color:white}}button:disabled{{opacity:.5;cursor:not-allowed}}
.notice{{color:#047857;font-weight:700}}.workspace{{display:grid;grid-template-columns:minmax(310px,0.9fr) minmax(270px,.75fr) minmax(420px,1.35fr);gap:14px;padding:14px;height:calc(100vh - 145px);box-sizing:border-box}}
.panel{{background:white;border-radius:14px;box-shadow:0 5px 22px #0f172a10;overflow:auto}}.panel>h2{{position:sticky;top:0;background:white;margin:0;padding:15px;border-bottom:1px solid #e5e7eb;font-size:17px;z-index:2}}
.upload-box{{margin:12px;padding:18px;border:2px dashed #fdba74;border-radius:12px;background:#fff7ed;text-align:center;cursor:pointer}}.upload-box.dragging{{border-color:#f97316;background:#ffedd5}}.upload-box strong,.upload-box span{{display:block}}.upload-box span{{font-size:12px;color:#64748b;margin-top:6px}}.empty{{margin:12px;padding:24px;text-align:center;color:#64748b;background:#f8fafc;border-radius:12px}}
.figures{{padding:12px;display:grid;gap:12px}}.figure{{border:1px solid #e5e7eb;border-radius:12px;overflow:hidden}}.figure img{{width:100%;display:block;background:#f8fafc}}.figure .body{{padding:10px}}.figure h2{{font-size:15px;margin:7px 0}}.figure p{{font-size:12px;color:#64748b;margin:5px 0}}.pick{{color:#c2410c;font-weight:700}}select{{width:100%;padding:8px;border:1px solid #d1d5db;border-radius:8px;background:white}}
.chapters{{list-style:none;padding:12px;margin:0;display:grid;gap:9px}}.chapters li{{padding:11px;border-radius:9px;background:#f8fafc}}.chapters strong,.chapters span{{display:block}}.chapters strong{{font-size:13px}}.chapters span{{font-size:12px;color:#c2410c;margin-top:5px}}
.preview-head{{padding:10px;border-bottom:1px solid #e5e7eb}}iframe{{width:100%;height:calc(100% - 54px);border:0;background:#eef1f5}}.inherit{{font-size:12px;color:#64748b}}
@media(max-width:1100px){{.workspace{{grid-template-columns:1fr 1fr;height:auto}}.preview-panel{{grid-column:1/-1;height:760px}}}}@media(max-width:720px){{.workspace{{display:block}}.panel{{margin-bottom:12px;max-height:none}}.preview-panel{{height:650px}}}}
</style></head><body><header><div class="top"><h1>双平台配图工作台</h1><div class="modes">
<button class="mode active" data-mode="shared">两端共用</button><button class="mode" data-mode="wechat">公众号微调</button><button class="mode" data-mode="toutiao">今日头条微调</button><span id="inherit" class="inherit"></span></div></div>
<p>把图片拖到左侧或点击选择，勾选“用于正文”并指定位置。保存不会上传平台，点击“确认配图”后才允许同步草稿。</p>
<div class="actions"><button id="save" class="primary">保存当前方案</button><button id="reset">恢复为共用方案</button><button id="confirm" class="confirm">确认配图</button><span class="notice" id="notice"></span></div></header>
<main class="workspace"><section class="panel"><h2>候选图片</h2><div id="upload" class="upload-box"><strong>点击选择图片，或拖到这里</strong><span>支持 PNG、JPG、GIF、WebP；单张不超过 25MB</span><input id="file-input" type="file" accept="image/png,image/jpeg,image/gif,image/webp" multiple hidden></div>{'' if cards else '<div class="empty">还没有图片，请先从电脑中选择。</div>'}<div class="figures">{''.join(cards)}</div></section>
<section class="panel"><h2>文章位置</h2><ul class="chapters">{heading_list}</ul></section>
<section class="panel preview-panel"><div class="preview-head"><div class="preview-tabs"><button class="preview-tab active" data-src="/pd-workflow/preview/wechat">公众号预览</button><button class="preview-tab" data-src="/pd-workflow/preview/toutiao">今日头条预览</button></div></div><iframe id="preview" src="/pd-workflow/preview/wechat"></iframe></section></main>
<script id="workflow-data" type="application/json">{payload}</script><script>
const data=JSON.parse(document.getElementById('workflow-data').textContent);let mode='shared';
const cards=[...document.querySelectorAll('.figure')];
function loadMode(next){{mode=next;document.querySelectorAll('.mode').forEach(x=>x.classList.toggle('active',x.dataset.mode===mode));const plan=data.plans[mode]||[];const byId=new Map(plan.map(x=>[x.id,x]));cards.forEach(card=>{{const item=byId.get(card.dataset.id);card.querySelector('input').checked=!!item;if(item)card.querySelector('select').value=item.before_heading;}});document.getElementById('reset').style.display=mode==='shared'?'none':'';document.getElementById('inherit').textContent=mode!=='shared'&&data.inherited[mode]?'当前继承共用方案':'当前为独立微调';refreshChapters();}}
function collect(){{return cards.filter(card=>card.querySelector('input').checked).map(card=>({{id:card.dataset.id,before_heading:card.querySelector('select').value}}));}}
function refreshChapters(){{const groups={{}};collect().forEach(item=>(groups[item.before_heading]??=[]).push(item.id));document.querySelectorAll('.chapters li').forEach(li=>li.querySelector('span').textContent=(groups[li.dataset.heading]||[]).join('、'));}}
cards.forEach(card=>{{card.querySelector('input').addEventListener('change',refreshChapters);card.querySelector('select').addEventListener('change',refreshChapters);}});document.querySelectorAll('.mode').forEach(button=>button.addEventListener('click',()=>loadMode(button.dataset.mode)));
async function post(url,payload){{const response=await fetch(url,{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}});const result=await response.json();if(!response.ok)throw new Error(result.error||'操作失败');return result;}}
function fileBase64(file){{return new Promise((resolve,reject)=>{{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',',2)[1]||'');reader.onerror=()=>reject(new Error('无法读取图片'));reader.readAsDataURL(file);}});}}
async function uploadFiles(fileList){{const files=[...fileList];if(!files.length)return;const upload=document.getElementById('upload');const notice=document.getElementById('notice');upload.style.pointerEvents='none';try{{for(let i=0;i<files.length;i++){{const file=files[i];notice.textContent=`正在加入 ${{i+1}}/${{files.length}}：${{file.name}}`;if(file.size>25*1024*1024)throw new Error(`${{file.name}} 超过25MB`);await post('/pd-workflow/figures/upload',{{filename:file.name,data_base64:await fileBase64(file)}});}}notice.textContent=`已加入 ${{files.length}} 张图片，正在刷新……`;location.reload();}}catch(error){{alert(error.message);notice.textContent='';upload.style.pointerEvents='';}}}}
const upload=document.getElementById('upload'),fileInput=document.getElementById('file-input');upload.addEventListener('click',()=>fileInput.click());fileInput.addEventListener('change',()=>uploadFiles(fileInput.files));['dragenter','dragover'].forEach(name=>upload.addEventListener(name,event=>{{event.preventDefault();upload.classList.add('dragging');}}));['dragleave','drop'].forEach(name=>upload.addEventListener(name,event=>{{event.preventDefault();upload.classList.remove('dragging');}}));upload.addEventListener('drop',event=>uploadFiles(event.dataTransfer.files));
document.getElementById('save').addEventListener('click',async()=>{{try{{const result=await post('/pd-workflow/figures/apply',{{platform:mode,plan:collect()}});data.plans[mode]=collect();if(mode==='shared'){{if(data.inherited.wechat)data.plans.wechat=[...data.plans.shared];if(data.inherited.toutiao)data.plans.toutiao=[...data.plans.shared];}}else{{data.inherited[mode]=false}}document.getElementById('notice').textContent=result.message;document.getElementById('preview').contentWindow.location.reload();if(window.opener)window.opener.location.reload();loadMode(mode);}}catch(error){{alert(error.message)}}}});
document.getElementById('reset').addEventListener('click',async()=>{{try{{const result=await post('/pd-workflow/figures/reset',{{platform:mode}});data.inherited[mode]=true;data.plans[mode]=[...data.plans.shared];document.getElementById('notice').textContent=result.message;loadMode(mode);document.getElementById('preview').contentWindow.location.reload();}}catch(error){{alert(error.message)}}}});
document.getElementById('confirm').addEventListener('click',async()=>{{try{{const result=await post('/pd-workflow/figures/confirm',{{}});document.getElementById('notice').textContent=result.message;}}catch(error){{alert(error.message)}}}});
document.querySelectorAll('.preview-tab').forEach(button=>button.addEventListener('click',()=>{{document.querySelectorAll('.preview-tab').forEach(x=>x.classList.remove('active'));button.classList.add('active');document.getElementById('preview').src=button.dataset.src;}}));loadMode('shared');
</script></body></html>"""

    def result_html(self, message: str = "", error: str = "") -> str:
        result = self.last_result
        layout = result.get("layout") if isinstance(result.get("layout"), dict) else {}
        content_synced = bool(result.get("content_synced"))
        sync_blocked = bool(result.get("sync_blocked"))
        sync_issues = result.get("sync_issues")
        if not isinstance(sync_issues, list):
            sync_issues = []
        if sync_blocked:
            status = "正文未通过结构检查，已保存候选稿，暂不允许同步。"
        elif content_synced:
            status = "正文已同步回源文件，排版设置已保存，最终预览已生成。"
        else:
            status = "正文无变化，排版设置已保存，最终预览已生成。"
        details = [
            ("主题", str(layout.get("theme", ""))),
            ("主题色", str(layout.get("primaryColor", ""))),
            ("字号", str(layout.get("fontSize", ""))),
            ("首行缩进", "开启" if layout.get("isUseIndent") else "关闭"),
            ("两端对齐", "开启" if layout.get("isUseJustify") else "关闭"),
            (
                "源文件",
                "暂停同步"
                if sync_blocked
                else ("已联动" if content_synced else "无需变更"),
            ),
        ]
        detail_html = "".join(
            f"<li><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></li>"
            for label, value in details
        )
        notice = ""
        if message:
            notice = f'<div class="notice success">{html.escape(message)}</div>'
        if error:
            notice = f'<div class="notice error">{html.escape(error)}</div>'
        if sync_issues:
            issue_items = "".join(
                f"<li>{html.escape(str(issue))}</li>" for issue in sync_issues
            )
            notice += f'<div class="notice error"><strong>需要检查：</strong><ul>{issue_items}</ul></div>'
        editor_url = (
            "http://127.0.0.1:8800/md/"
            f"?pdWorkflow={self.workflow_id}"
        )
        return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>双平台文章工作流</title>
<style>
body{{margin:0;background:#f4f5f7;color:#1f2937;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif}}
.shell{{max-width:1080px;margin:0 auto;padding:28px}}
.card{{background:#fff;border-radius:16px;padding:24px;box-shadow:0 10px 35px #11182712}}
h1{{margin:0 0 8px;font-size:25px}}p{{line-height:1.75}}
ul{{list-style:none;padding:0;display:grid;grid-template-columns:repeat(5,1fr);gap:10px}}
li{{padding:12px;background:#fff7f2;border-radius:10px}}li span,li strong{{display:block}}li span{{font-size:12px;color:#6b7280}}li strong{{margin-top:4px}}
.actions{{display:flex;gap:12px;margin:20px 0;flex-wrap:wrap}}
button,a.button{{border:0;border-radius:9px;padding:11px 16px;text-decoration:none;cursor:pointer;font-size:15px}}
button{{background:#ff6a2a;color:#fff}}button:disabled{{opacity:.45;cursor:not-allowed}}
a.button{{background:#111827;color:#fff}}
.notice{{padding:12px 14px;border-radius:9px;margin:14px 0}}.success{{background:#ecfdf5;color:#047857}}.error{{background:#fef2f2;color:#b91c1c}}
iframe{{width:100%;height:72vh;border:1px solid #e5e7eb;border-radius:12px;background:#fff}}
@media(max-width:760px){{.shell{{padding:12px}}ul{{grid-template-columns:1fr 1fr}}}}
</style>
</head>
<body>
<main class="shell">
  <section class="card">
    <h1>本地排版已保存</h1>
    <p>{html.escape(status)}</p>
    {notice}
    <ul>{detail_html}</ul>
    <div class="actions">
      <a class="button" href="{html.escape(editor_url)}">返回排版编辑器</a>
      <a class="button" href="/pd-workflow/figure-tray" target="_blank">打开双平台配图工作台</a>
    </div>
    <iframe src="/pd-workflow/preview" title="最终公众号预览"></iframe>
  </section>
</main>
</body>
</html>"""


def make_handler(workflow: EditorWorkflow):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, _format: str, *_args: object) -> None:
            return

        def send_bytes(
            self,
            data: bytes,
            *,
            status: int = 200,
            content_type: str = "text/html; charset=utf-8",
        ) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:8800")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            self.end_headers()
            self.wfile.write(data)

        def send_json(self, payload: dict[str, object], status: int = 200) -> None:
            self.send_bytes(
                json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                status=status,
                content_type="application/json; charset=utf-8",
            )

        def do_OPTIONS(self) -> None:
            self.send_bytes(b"", status=204)

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/status":
                self.send_json(
                    {
                        "ready": True,
                        "workflow_id": workflow.workflow_id,
                        "article": str(workflow.article_path),
                    }
                )
                return
            if path == "/article":
                self.send_json({"markdown": workflow.editor_body()})
                return
            if path == "/figure-tray":
                try:
                    self.send_bytes(workflow.figure_tray_html().encode("utf-8"))
                except Exception as error:
                    self.send_bytes(str(error).encode("utf-8"), status=400)
                return
            if path.startswith("/asset/"):
                try:
                    figure_id = path.rsplit("/", 1)[-1]
                    asset = workflow.figure_asset(figure_id)
                    content_type = mimetypes.guess_type(asset.name)[0] or "application/octet-stream"
                    self.send_bytes(asset.read_bytes(), content_type=content_type)
                except Exception as error:
                    self.send_bytes(str(error).encode("utf-8"), status=404)
                return
            if path in {"/preview", "/preview/wechat"}:
                try:
                    rendered = render_article(str(workflow.article_path))
                    self.send_bytes(Path(rendered["preview_path"]).read_bytes())
                except Exception as error:
                    self.send_bytes(str(error).encode("utf-8"), status=400)
                return
            if path == "/preview/toutiao":
                try:
                    rendered = render_toutiao(str(workflow.article_path))
                    self.send_bytes(Path(rendered["preview_path"]).read_bytes())
                except Exception as error:
                    self.send_bytes(str(error).encode("utf-8"), status=400)
                return
            if path in {"/", "/result"}:
                self.send_bytes(workflow.result_html().encode("utf-8"))
                return
            self.send_bytes("页面不存在".encode("utf-8"), status=404)

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            if path == "/handoff":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length <= 0 or length > 2_000_000:
                        raise RuntimeError("排版数据大小异常")
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                    if not isinstance(payload, dict):
                        raise RuntimeError("排版数据格式异常")
                    self.send_json(workflow.save_handoff(payload))
                except Exception as error:
                    self.send_json({"error": str(error)}, status=400)
                return
            if path == "/figures/apply":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length <= 0 or length > 500_000:
                        raise RuntimeError("配图计划大小异常")
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                    if not isinstance(payload, dict):
                        raise RuntimeError("配图计划格式异常")
                    self.send_json(workflow.apply_figures(payload))
                except Exception as error:
                    self.send_json({"error": str(error)}, status=400)
                return
            if path == "/figures/upload":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length <= 0 or length > 36_000_000:
                        raise RuntimeError("图片传输大小异常")
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                    if not isinstance(payload, dict):
                        raise RuntimeError("图片数据格式异常")
                    self.send_json(workflow.upload_figure(payload))
                except Exception as error:
                    self.send_json({"error": str(error)}, status=400)
                return
            if path == "/figures/reset":
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                    if not isinstance(payload, dict):
                        raise RuntimeError("配图计划格式异常")
                    self.send_json(workflow.reset_figures(payload))
                except Exception as error:
                    self.send_json({"error": str(error)}, status=400)
                return
            if path == "/figures/confirm":
                try:
                    self.send_json(workflow.confirm_figure_plan())
                except Exception as error:
                    self.send_json({"error": str(error)}, status=400)
                return
            if path == "/publish":
                self.send_json(
                    {"error": "本地工作台不再直接上传；请先确认配图，再执行“同步双平台草稿”。"},
                    status=409,
                )
                return
            self.send_bytes("页面不存在".encode("utf-8"), status=404)

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description="doocs/md 与双平台文章工作流本地桥接")
    parser.add_argument("--article", required=True)
    parser.add_argument("--port", type=int, default=8788)
    args = parser.parse_args()
    try:
        workflow = EditorWorkflow(args.article, args.port)
        server = ThreadingHTTPServer(
            ("127.0.0.1", args.port),
            make_handler(workflow),
        )
        print(
            f"排版工作流桥接：{workflow.base_url}/status",
            flush=True,
        )
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
