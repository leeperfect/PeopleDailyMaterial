#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""下载并固定 doocs/md 渲染器；无需 IDE。"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from modules.writing_workflow import load_public_config, project_path


def installed_revision(target: Path) -> str:
    marker = target / ".peopledaily-revision"
    return marker.read_text(encoding="utf-8").strip() if marker.exists() else ""


def apply_offline_patch(target: Path) -> None:
    """写入项目固定预设，并禁用 MCP 代码主题的远程抓取。

    代码块的 stackoverflow-light 外观由项目内 CSS 资产提供；
    完整编辑器默认使用小米橙、首行缩进和两端对齐。
    """
    config_path = target / "packages" / "mcp-server" / "src" / "config-options.ts"
    source = config_path.read_text(encoding="utf-8")
    original = "codeBlockTheme: codeBlockThemeOptions[0].value,"
    patched = "codeBlockTheme: undefined,"
    if original in source:
        config_path.write_text(source.replace(original, patched, 1), encoding="utf-8")
    elif patched not in source:
        raise RuntimeError("无法应用 doocs/md 离线代码主题补丁")

    style_path = target / "packages" / "shared" / "src" / "configs" / "style.ts"
    style_source = style_path.read_text(encoding="utf-8")
    style_source = style_source.replace(
        "primaryColor: colorOptions[0].value,",
        "primaryColor: `#ff6a2a`,",
        1,
    )
    style_path.write_text(style_source, encoding="utf-8")

    store_path = target / "apps" / "web" / "src" / "stores" / "theme.ts"
    store_source = store_path.read_text(encoding="utf-8")
    store_source = store_source.replace(
        "const isUseIndent = store.reactive(addPrefix(`use_indent`), false)",
        "const isUseIndent = store.reactive(addPrefix(`use_indent`), true)",
        1,
    ).replace(
        "const isUseJustify = store.reactive(addPrefix(`use_justify`), false)",
        "const isUseJustify = store.reactive(addPrefix(`use_justify`), true)",
        1,
    ).replace(
        "isUseIndent.value = false",
        "isUseIndent.value = true",
        1,
    ).replace(
        "isUseJustify.value = false",
        "isUseJustify.value = true",
        1,
    )
    store_path.write_text(store_source, encoding="utf-8")


def download_source(target: Path, revision: str) -> None:
    url = f"https://codeload.github.com/doocs/md/tar.gz/{revision}"
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="doocs-md-") as temporary:
        archive = Path(temporary) / "doocs-md.tar.gz"
        print("正在下载固定版本的 doocs/md……")
        result = subprocess.run(
            [
                "curl",
                "-L",
                "--http1.1",
                "--fail",
                "--retry",
                "2",
                "--connect-timeout",
                "20",
                "--output",
                str(archive),
                url,
            ],
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError("doocs/md 下载失败，请检查网络后重试")
        extract_root = Path(temporary) / "extract"
        extract_root.mkdir()
        with tarfile.open(archive, "r:gz") as package:
            package.extractall(extract_root, filter="data")
        candidates = [item for item in extract_root.iterdir() if item.is_dir()]
        if len(candidates) != 1:
            raise RuntimeError("doocs/md 源码包结构异常")
        if target.exists():
            shutil.rmtree(target)
        shutil.move(str(candidates[0]), target)
        apply_offline_patch(target)
        (target / ".peopledaily-revision").write_text(
            revision + "\n",
            encoding="utf-8",
        )


def install_dependencies(target: Path) -> None:
    if not shutil.which("node") or not shutil.which("pnpm"):
        raise RuntimeError("需要 Node.js 和 pnpm；当前环境未找到其中至少一个")
    print("正在安装 doocs/md 本地依赖……")
    result = subprocess.run(
        ["pnpm", "install", "--frozen-lockfile", "--ignore-scripts"],
        cwd=target,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("doocs/md 依赖安装失败")


def setup(force: bool = False) -> Path:
    config = load_public_config()
    settings = config["doocs"]
    target = project_path(settings["local_dir"])
    revision = settings["revision"]
    if force or installed_revision(target) != revision:
        download_source(target, revision)
    mcp_modules = target / "packages" / "mcp-server" / "node_modules"
    if force or not mcp_modules.exists():
        install_dependencies(target)
    print(f"doocs/md 已就绪：{target}")
    print(f"固定版本：{revision}")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="准备 doocs/md 本地渲染器")
    parser.add_argument("--force", action="store_true", help="重新下载并安装")
    args = parser.parse_args()
    try:
        setup(force=args.force)
    except Exception as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
