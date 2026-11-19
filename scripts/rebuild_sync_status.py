#!/usr/bin/env python3
"""旧入口已退役：本地存档不能用作远端同步凭证。"""

if __name__ == '__main__':
    raise SystemExit('旧状态重建已停用，未读取或写入同步记录。请用 python3 scripts/notion_maintenance.py --dry-run 核对远端页面。')
