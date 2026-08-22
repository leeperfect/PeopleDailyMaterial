const { MarkdownView, Notice, Plugin, normalizePath } = require("obsidian");

const ARTICLE_ROOTS = [
  "data/articles/人民日报系列/",
  "data/articles/热点系列/",
  "data/articles/往期文章/人民日报系列/",
  "data/articles/往期文章/热点系列/",
];

const SUPPORTED_MIME = new Map([
  ["image/png", ".png"],
  ["image/jpeg", ".jpg"],
  ["image/gif", ".gif"],
  ["image/webp", ".webp"],
]);

function articleNumber(file) {
  const match = file.basename.match(/^(?:热点)?(\d+)-/);
  return match ? match[1] : null;
}

function articleDate(app, file) {
  const raw = app.metadataCache.getFileCache(file)?.frontmatter?.date;
  if (typeof raw === "string" && /^\d{4}-\d{2}-\d{2}$/.test(raw)) return raw;
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60_000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

function isArticle(file) {
  return Boolean(file && ARTICLE_ROOTS.some((root) => file.path.startsWith(root)));
}

function arrayBufferFromBuffer(buffer) {
  return buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength);
}

class ArticleImagePastePlugin extends Plugin {
  async onload() {
    this.registerDomEvent(document, "paste", (event) => this.handlePaste(event), true);
    this.addCommand({
      id: "show-paste-status",
      name: "检查文章配图粘贴功能",
      callback: () => new Notice("文章配图粘贴已启用：请在成稿中粘贴 PPT 图片。"),
    });
  }

  async handlePaste(event) {
    const view = this.app.workspace.getActiveViewOfType(MarkdownView);
    const file = view?.file;
    if (!view || !isArticle(file)) return;
    if (!(event.target instanceof Element) || !event.target.closest(".cm-editor")) return;

    const number = articleNumber(file);
    if (!number) {
      return;
    }
    if (!this.hasClipboardImage(event)) return;

    // 必须在第一次异步读取之前阻止 Obsidian 的默认粘贴，否则会同时生成两份附件。
    event.preventDefault();
    event.stopPropagation();

    try {
      const images = await this.clipboardImages(event);
      if (!images.length) throw new Error("剪贴板中的内容无法转换为图片");
      const date = articleDate(this.app, file);
      const folder = normalizePath(`media/images/${date}-article-${number}`);
      await this.ensureFolder(folder);
      const links = [];
      for (const image of images) {
        const target = this.nextImagePath(folder, number, image.extension);
        await this.app.vault.createBinary(target, image.data);
        const sequence = target.match(/-(\d{2})\.[^.]+$/)?.[1] || "";
        const alt = `第${number}篇配图${sequence}`;
        links.push(`![${alt}](${target})`);
      }
      this.insertImageBlocks(view.editor, links);
      new Notice(`已保存并插入 ${links.length} 张第${number}篇配图。`);
    } catch (error) {
      console.error("文章配图粘贴失败", error);
      new Notice(`图片粘贴失败：${error?.message || String(error)}`, 8000);
    }
  }

  hasClipboardImage(event) {
    const items = Array.from(event.clipboardData?.items || []);
    if (items.some((item) => item.kind === "file" && SUPPORTED_MIME.has(item.type))) {
      return true;
    }
    try {
      const { clipboard } = require("electron");
      return !clipboard.readImage().isEmpty();
    } catch (_) {
      return false;
    }
  }

  async clipboardImages(event) {
    const result = [];
    const items = Array.from(event.clipboardData?.items || []);
    for (const item of items) {
      if (item.kind !== "file" || !item.type.startsWith("image/")) continue;
      const file = item.getAsFile();
      const extension = SUPPORTED_MIME.get(item.type);
      if (!file || !extension) continue;
      result.push({ data: await file.arrayBuffer(), extension });
    }
    if (result.length) return result;

    // PowerPoint 在 macOS 上有时只向系统剪贴板提供 TIFF/幻灯片位图，
    // Electron 可把这类内容稳定转成 PNG，避免用户先导出图片。
    try {
      const { clipboard } = require("electron");
      const nativeImage = clipboard.readImage();
      if (!nativeImage.isEmpty()) {
        const png = nativeImage.toPNG();
        return [{ data: arrayBufferFromBuffer(png), extension: ".png" }];
      }
    } catch (error) {
      console.debug("系统剪贴板没有可转换的图片", error);
    }
    return [];
  }

  async ensureFolder(folder) {
    let current = "";
    for (const part of folder.split("/")) {
      current = current ? `${current}/${part}` : part;
      if (!this.app.vault.getAbstractFileByPath(current)) {
        await this.app.vault.createFolder(current);
      }
    }
  }

  nextImagePath(folder, number, extension) {
    for (let sequence = 1; sequence <= 999; sequence += 1) {
      const candidate = normalizePath(
        `${folder}/fig-${number}-${String(sequence).padStart(2, "0")}${extension}`,
      );
      if (!this.app.vault.getAbstractFileByPath(candidate)) return candidate;
    }
    throw new Error("本篇图片编号已超过999张");
  }

  insertImageBlocks(editor, links) {
    const cursor = editor.getCursor();
    const line = editor.getLine(cursor.line);
    const before = cursor.ch === 0 && line.trim() === "" ? "" : "\n\n";
    editor.replaceSelection(`${before}${links.join("\n\n")}\n\n`);
  }
}

module.exports = ArticleImagePastePlugin;
