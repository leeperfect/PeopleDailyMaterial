"""Notion 页面身份索引：稳定 ID 优先，证据不足不自动改页。"""


class AmbiguousArticleMatch(ValueError):
    """不能可靠地匹配到一个页面；保留现状，交由人工核对。"""


def _keys(article):
    title, date = article.get("title"), article.get("date")
    return {
        "article_id": article.get("article_id") or article.get("Article ID"),
        "url": article.get("source_url") or article.get("url"),
        "title_date": (title, date) if title and date else None,
    }


def build_existing_indexes(existing_articles):
    indexes = {"pages": {}, "article_id": {}, "url": {}, "title_date": {}}
    for article in existing_articles:
        add_to_indexes(article, article["id"], indexes)
    return indexes


def add_to_indexes(article, page_id, indexes):
    # 同一页补齐 ID / 更新标题后，不能让旧键继续指向该页。
    old = indexes["pages"].get(page_id)
    if old is not None:
        for field, value in _keys(old).items():
            if value:
                bucket = indexes[field][value]
                bucket.discard(page_id)
                if not bucket:
                    del indexes[field][value]
    keys = _keys(article)
    record = {"id": page_id, "article_id": keys["article_id"], "url": keys["url"],
              "title": article.get("title"), "date": article.get("date")}
    indexes["pages"][page_id] = record
    for field, value in keys.items():
        if value:
            indexes[field].setdefault(value, set()).add(page_id)


def find_duplicate(article, indexes):
    keys = _keys(article)
    for field in ("article_id", "url", "title_date"):
        ids = indexes[field].get(keys[field], ())
        if not ids:
            continue
        if field == "title_date":
            # 不同 ID 或不同 URL 的同名文章是独立资料。仅标题日期吻合的
            # 老页也不能贸然覆盖或重复新建，留待人工补齐身份。
            for page_id in ids:
                other = indexes["pages"][page_id]
                if not any(keys[k] and other[k] and keys[k] != other[k] for k in ("article_id", "url")):
                    raise AmbiguousArticleMatch("仅日期和标题相同，缺少可核对的 Article ID 或来源链接")
            continue
        if len(ids) != 1:
            raise AmbiguousArticleMatch(f"多个页面共用同一 {field}")
        page = indexes["pages"][next(iter(ids))]
        if field == "url" and keys["article_id"] and page["article_id"] and keys["article_id"] != page["article_id"]:
            raise AmbiguousArticleMatch("来源链接相同但 Article ID 冲突")
        return page
    return None
