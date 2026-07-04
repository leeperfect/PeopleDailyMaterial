---
type: writing_workflow
updated: 2026-07-04
scope: PeopleDailyMaterial
---

# 公众号写作、二次润色与草稿箱工作流

这套流程把 Codex 写作、Humanizer-zh、得到大脑二润、doocs/md 排版和公众号草稿箱连成一条线。日常只需要用自然语言告诉 Codex当前要做哪一步，不需要打开 IDE。

## 日常操作

### 第一次准备

对 Codex说：

> 配置公众号写作工作流。

Codex会检查 Get笔记、固定封面和 doocs/md。doocs/md 固定在 `writing_workflow.json` 记录的版本，安装在被 Git 忽略的 `.local/doocs-md/`。

### 写完并送去二润

对 Codex说：

> 把这篇文章写完并送去二润。

Codex执行：

1. 完成文章初稿。
2. 保存 `00-draft.md` 初稿快照。
3. 调用 Humanizer-zh 润色正文，保留 YAML、事实、数字、来源和教学框架。
4. 保存 `01-humanizer.md` 快照。
5. 只把标题和正文送入得到大脑，并记录真实 `note_id`。

得到笔记标题包含 `[PD-工作流编号]`，不会靠标题猜测文章身份。

### 从得到大脑拉回

你在 App 中完成二润后，对 Codex说：

> 我在得到改好了，拉回。

拉回前会检查：

- 正文是否真的发生变化；
- 是否异常缩短；
- 一级标题是否丢失；
- 参考文章/资料来源栏目是否丢失；
- 原有来源链接是否丢失。

校验不通过时只保存候选稿和差异报告，不覆盖本地成稿。YAML 始终保留在本地，不参与 App 润色。

### 预览排版

对 Codex说：

> 预览一下公众号排版。

Codex使用 doocs/md 生成只读成品页，通过仅监听 `127.0.0.1` 的临时服务在内置浏览器打开。页面带“复制公众号富文本”按钮，既可检查，也可作为接口不可用时的兜底。

默认排版：

- 经典主题；
- 无衬线字体、16px；
- 主题色 `#ff6a2a`；
- H2 默认样式、图注仅使用 alt；
- 代码主题使用截图中的 stackoverflow-light；
- Mac 代码样式开启、行号关闭；
- 外链转引用关闭；
- 首行缩进和两端对齐开启。

需要换主题时说：

> 打开完整排版编辑器。

Codex在后台启动 doocs/md 并在内置浏览器载入文章。确定后说“把这个排版保存为本文设置”，单篇设置会写入本地工作流状态；下一次预览和发布继续使用它。

### 同步公众号草稿箱

对 Codex说：

> 同步到公众号草稿箱。

同步过程：

1. 使用同一份 doocs/md HTML；
2. 按文章系列自动选择固定封面；
3. 上传本地正文图片并换成微信素材地址；
4. 作者固定为 `LeePerfect`；
5. 创建草稿并记录 `media_id`；
6. 不调用群发接口。

相同正文和排版已创建过草稿时，流程会停止重复同步，除非你明确要求重新创建。

## 公众号接口首次启用

第一次同步时，Codex一次只引导一个步骤：

1. 在内置浏览器打开微信公众平台，等待你扫码。
2. 引导进入“设置与开发 → 基本配置”。
3. 引导找到 AppID，并启用或重置 AppSecret。
4. 打开仅监听本机的私密配置页：

   ```bash
   python3 scripts/writing_workflow.py setup-wechat
   ```

5. 你在密码框填写凭证。密钥只保存到 `.env`，不进入聊天、日志和 Git。
6. Codex查询当前公网 IP，引导加入 IP 白名单。
7. Codex验证 access_token。
8. Codex调用只读的草稿数量接口检查权限，不创建测试草稿。

若账号没有草稿接口权限，Codex改用内置浏览器登录公众号后台，自动填写标题、作者、摘要、封面和富文本正文。若公众号页面变化导致自动代填失败，则使用只读预览页的一键复制按钮。

## 固定封面

| 文章系列 | 本地文件 |
|---|---|
| 人民日报系列 | `media/images/wechat-fixed-covers/people-daily-header.png` |
| 热点系列 | `media/images/wechat-fixed-covers/hotspot-header.png` |

封面真实文件由网盘同步，不进入 Git；文字索引见 `media/_index.md`。

## 状态和版本

- 本地机器状态：`data/core/writing_workflow_state.json`，已忽略。
- access_token 缓存：`data/exports/wechat_token_cache.json`，已忽略。
- 一润稿、拉回前稿、二润候选稿和差异报告：
  `data/analysis/日期/writing-workflow/工作流编号/`。
- 临时 HTML 预览：`/tmp/peopledaily-writing-preview/`，不进入项目。

Markdown 成品稿始终是最终事实源；得到大脑只承担二润中转。

## 命令速查

通常由 Codex代为执行：

```bash
python3 scripts/writing_workflow.py doctor "<文章路径>"
python3 scripts/writing_workflow.py setup-doocs
python3 scripts/writing_workflow.py snapshot "<文章路径>" --stage draft
python3 scripts/writing_workflow.py send "<文章路径>"
python3 scripts/writing_workflow.py pull "<文章路径>"
python3 scripts/writing_workflow.py preview "<文章路径>"
python3 scripts/writing_workflow.py editor "<文章路径>"
python3 scripts/writing_workflow.py save-layout "<文章路径>" --theme grace
python3 scripts/writing_workflow.py setup-wechat
python3 scripts/writing_workflow.py wechat-preflight
python3 scripts/writing_workflow.py publish "<文章路径>" --dry-run
python3 scripts/writing_workflow.py publish "<文章路径>"
python3 scripts/writing_workflow.py status "<文章路径>"
```

## 安全边界

- AppSecret、Get笔记密钥、access_token 不写入文章、日志或 Git。
- 不自动 Git commit。
- 不自动群发。
- 浏览器自动代填只在你明确要求“同步草稿箱”后执行。
