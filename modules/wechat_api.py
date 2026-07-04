#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""微信公众号接口的最小安全封装，不记录或输出密钥与 access_token。"""

from __future__ import annotations

import hashlib
import io
import json
import mimetypes
import os
import time
from pathlib import Path
from typing import Any

import requests

from modules.writing_workflow import (
    atomic_write_json,
    load_dotenv_values,
    load_public_config,
    project_path,
)


TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
MATERIAL_ADD_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material"
CONTENT_IMAGE_URL = "https://api.weixin.qq.com/cgi-bin/media/uploadimg"
DRAFT_ADD_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"


class WechatApiError(RuntimeError):
    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code


def credentials() -> tuple[str, str]:
    values = load_dotenv_values()
    app_id = os.environ.get("WECHAT_APPID") or values.get("WECHAT_APPID", "")
    app_secret = os.environ.get("WECHAT_APPSECRET") or values.get("WECHAT_APPSECRET", "")
    if not app_id or not app_secret:
        raise WechatApiError("公众号接口尚未配置，请先启动首次启用向导")
    return app_id, app_secret


def explain_error(code: int | None, message: str) -> str:
    known = {
        40001: "AppSecret 或 access_token 无效",
        40013: "AppID 无效",
        40164: "当前公网 IP 不在公众号白名单",
        48001: "当前公众号没有调用该接口的权限",
        45009: "接口调用次数超过当日限制",
    }
    prefix = known.get(code, "微信公众号接口调用失败")
    return f"{prefix}（{code}）：{message}" if code is not None else f"{prefix}：{message}"


def response_json(response: requests.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except ValueError as error:
        raise WechatApiError(f"微信公众号返回非 JSON 数据（HTTP {response.status_code}）") from error
    if not isinstance(data, dict):
        raise WechatApiError("微信公众号返回结构异常")
    if data.get("errcode") not in (None, 0):
        code = data.get("errcode")
        raise WechatApiError(explain_error(code, str(data.get("errmsg", ""))), code)
    return data


def token_cache_path() -> Path:
    config = load_public_config()
    return project_path(config["wechat"]["token_cache"])


def get_access_token(*, force: bool = False) -> str:
    cache_path = token_cache_path()
    if not force and cache_path.exists():
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            if cache.get("expires_at", 0) > time.time() + 300:
                return str(cache["access_token"])
        except (json.JSONDecodeError, OSError, KeyError):
            pass

    app_id, app_secret = credentials()
    try:
        response = requests.get(
            TOKEN_URL,
            params={
                "grant_type": "client_credential",
                "appid": app_id,
                "secret": app_secret,
            },
            timeout=15,
        )
    except requests.RequestException as error:
        raise WechatApiError(f"获取 access_token 时网络异常：{error}") from error
    data = response_json(response)
    token = data.get("access_token")
    if not token:
        raise WechatApiError("微信公众号没有返回 access_token")
    atomic_write_json(
        cache_path,
        {
            "access_token": token,
            "expires_at": time.time() + int(data.get("expires_in", 7200)),
        },
    )
    try:
        os.chmod(cache_path, 0o600)
    except OSError:
        pass
    return str(token)


def public_ip() -> str:
    try:
        response = requests.get("https://api.ipify.org", timeout=10)
        response.raise_for_status()
    except requests.RequestException as error:
        raise WechatApiError(f"查询公网 IP 失败：{error}") from error
    return response.text.strip()


def draft_count() -> int:
    config = load_public_config()
    token = get_access_token()
    try:
        response = requests.get(
            config["wechat"]["draft_count_endpoint"],
            params={"access_token": token},
            timeout=15,
        )
    except requests.RequestException as error:
        raise WechatApiError(f"检查草稿箱权限时网络异常：{error}") from error
    data = response_json(response)
    return int(data.get("total_count", 0))


def upload_permanent_image(image_path: Path) -> str:
    token = get_access_token()
    mime = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
    try:
        with image_path.open("rb") as file:
            response = requests.post(
                MATERIAL_ADD_URL,
                params={"access_token": token, "type": "image"},
                files={"media": (image_path.name, file, mime)},
                timeout=60,
            )
    except (OSError, requests.RequestException) as error:
        raise WechatApiError(f"上传固定封面失败：{error}") from error
    data = response_json(response)
    media_id = data.get("media_id")
    if not media_id:
        raise WechatApiError("固定封面上传成功，但没有返回 media_id")
    return str(media_id)


def upload_content_image(image_path: Path) -> str:
    token = get_access_token()
    mime = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
    try:
        with image_path.open("rb") as file:
            response = requests.post(
                CONTENT_IMAGE_URL,
                params={"access_token": token},
                files={"media": (image_path.name, file, mime)},
                timeout=60,
            )
    except (OSError, requests.RequestException) as error:
        raise WechatApiError(f"上传正文图片失败：{image_path.name}：{error}") from error
    data = response_json(response)
    url = data.get("url")
    if not url:
        raise WechatApiError(f"正文图片 {image_path.name} 没有返回微信素材地址")
    return str(url)


def upload_remote_content_image(source_url: str) -> str:
    try:
        response = requests.get(source_url, timeout=30)
        response.raise_for_status()
    except requests.RequestException as error:
        raise WechatApiError(f"下载正文远程图片失败：{source_url}：{error}") from error
    content_type = response.headers.get("Content-Type", "").split(";", 1)[0]
    if not content_type.startswith("image/"):
        raise WechatApiError(f"正文远程地址不是图片：{source_url}")
    if len(response.content) > 10 * 1024 * 1024:
        raise WechatApiError(f"正文图片超过 10MB：{source_url}")
    filename = Path(urlparse_safe_path(source_url)).name or "article-image"
    token = get_access_token()
    try:
        upload_response = requests.post(
            CONTENT_IMAGE_URL,
            params={"access_token": token},
            files={"media": (filename, io.BytesIO(response.content), content_type)},
            timeout=60,
        )
    except requests.RequestException as error:
        raise WechatApiError(f"上传正文远程图片失败：{source_url}：{error}") from error
    data = response_json(upload_response)
    url = data.get("url")
    if not url:
        raise WechatApiError(f"正文远程图片没有返回微信素材地址：{source_url}")
    return str(url)


def urlparse_safe_path(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).path


def add_draft(article: dict[str, Any]) -> str:
    token = get_access_token()
    try:
        response = requests.post(
            DRAFT_ADD_URL,
            params={"access_token": token},
            json={"articles": [article]},
            timeout=60,
        )
    except requests.RequestException as error:
        raise WechatApiError(f"创建公众号草稿时网络异常：{error}") from error
    data = response_json(response)
    media_id = data.get("media_id")
    if not media_id:
        raise WechatApiError("公众号没有返回草稿 media_id")
    return str(media_id)


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
