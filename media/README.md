# 本地多媒体资产库

`media/` 用来放图片、课件、音视频、压缩包等非文本资产。这些文件通常体积较大，默认通过网盘同步，不进入 GitHub。

GitHub 只保留这个说明文件、`_index.md` 索引和空目录占位。真正的大文件放在对应分类目录里。

```text
media/
  _index.md        # 多媒体资产索引，记录主题、类型、路径、网盘位置
  images/          # 小红书图、公众号配图、封面图、素材图
  courseware/      # PPTX、Keynote、PDF 课件和讲义成品
  video/           # 口播、短视频、录屏、课程视频
  audio/           # 口播音频、课程音频、配音文件
  packages/        # 打包交付物、压缩包、整套发布包
```

推荐命名方式：

```text
media/images/2026-06-06-new-quality-productivity-xhs/
media/courseware/2026-06-06-new-quality-productivity-class/
media/video/2026-06-06-new-quality-productivity-short-video/
```

使用原则：

- 文字稿、选题、视觉 brief、讲稿提示继续放在 `data/analysis/` 或 `data/articles/公众号文章/`。
- 小红书图片、公众号配图、PPTX、视频、音频、压缩包放在 `media/`。
- 每新建一组多媒体资产，在 `_index.md` 里补一行，方便人和 AI 找到。
- 如果已经上传网盘，在 `_index.md` 里记录网盘文件夹名或分享链接。
- Markdown 文章里尽量记录“媒体位置”，不要直接嵌入大图片。
