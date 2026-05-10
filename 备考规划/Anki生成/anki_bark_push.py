#!/usr/bin/env python3
"""
Anki → Bark 随机抽卡推送

用法：
  python3 anki_bark_push.py            # 正式：抽卡 + 推送
  python3 anki_bark_push.py --dry-run  # 抽卡但只打印不推送（调试）
  python3 anki_bark_push.py --reset    # 清空当日去重记录

工作流：
  1. 连 AnkiConnect (localhost:8765)
  2. 在 deck:中哲::* 范围抽一张「已学过」（-is:new）的卡
  3. 高频标签卡（tag:高频）权重 ×2
  4. 当日已推过的卡不重复推
  5. 推送到 Bark：
       - title  : Front（清洁后截短 80）
       - subtitle: 卡组简称（如"老子"）
       - body   : Back（清洁后，顶部加分隔提示）
"""

import json
import os
import sys
import re
import random
import urllib.request
import urllib.error
from datetime import date
from html import unescape
from pathlib import Path

# ===== 关键：launchd 子进程不继承 NO_PROXY，必须在脚本里硬编码 =====
# 否则系统代理（Surge/Clash 等）会把 localhost:8765 也代理掉，返回 502。
os.environ["NO_PROXY"] = "localhost,127.0.0.1,::1,.local,api.day.app"
os.environ["no_proxy"] = "localhost,127.0.0.1,::1,.local,api.day.app"

# ===== 配置 =====
ANKI_URL = "http://localhost:8765"
BARK_URL = "https://api.day.app/TAi52BtPSQdAZocv3v2gNX"
DECK_QUERY = 'deck:"中哲::《中国哲学史》——郭齐勇::*" -is:new'   # 抽卡范围：郭齐勇标准卡组中已学过的
HIGH_FREQ_BOOST = 2                         # 高频标签卡的抽中权重倍数
TITLE_MAX = 80
BODY_MAX = 1500
DEDUP_FILE = Path("/tmp/anki_bark_pushed_today.json")

DRY_RUN = "--dry-run" in sys.argv
RESET = "--reset" in sys.argv


def anki(action, **params):
    """调用 AnkiConnect。"""
    req = urllib.request.Request(
        ANKI_URL,
        data=json.dumps({"action": action, "version": 6, "params": params}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=5).read())
    except urllib.error.URLError as e:
        print(f"[ERR] AnkiConnect 连不上（Anki App 没开？）: {e}", file=sys.stderr)
        sys.exit(2)
    if resp.get("error"):
        print(f"[ERR] AnkiConnect 报错: {resp['error']}", file=sys.stderr)
        sys.exit(3)
    return resp["result"]


def clean_html(s: str) -> str:
    """把 Anki 的 HTML 字段清洗成手机通知好读的纯文本。"""
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.IGNORECASE)
    s = re.sub(r"<[^>]+>", "", s)            # 删除所有 HTML 标签（笔记里已用【】标重点，无需再加）
    s = unescape(s)
    s = re.sub(r"\n{3,}", "\n\n", s)         # 折叠多余空行
    return s.strip()


def deck_short_name(deck_name: str) -> str:
    """从完整 deckName 提取章节简称用作 subtitle。
    例: 中哲::《中国哲学史》——郭齐勇::老子_v1标准卡组 -> 老子
    """
    last = deck_name.rsplit("::", 1)[-1]
    return re.sub(r"_v\d+.*$", "", last)


def load_dedup() -> set:
    """加载今日已推过的 noteId 集合。"""
    if RESET and DEDUP_FILE.exists():
        DEDUP_FILE.unlink()
        print("[INFO] 已重置当日去重记录")
        return set()
    if not DEDUP_FILE.exists():
        return set()
    try:
        data = json.loads(DEDUP_FILE.read_text())
        if data.get("date") != str(date.today()):
            return set()                     # 跨日，作废
        return set(data.get("note_ids", []))
    except Exception:
        return set()


def save_dedup(pushed: set):
    DEDUP_FILE.write_text(json.dumps({"date": str(date.today()), "note_ids": list(pushed)}))


def push_bark(title: str, body: str, subtitle: str) -> bool:
    payload = {
        "title": title,
        "body": body,
        "subtitle": subtitle,
        "group": "Anki 抽查",
        "level": "active",
        "sound": "minuet",
    }
    req = urllib.request.Request(
        BARK_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=5).read())
    except urllib.error.URLError as e:
        print(f"[ERR] Bark 推送失败: {e}", file=sys.stderr)
        return False
    if resp.get("code") != 200:
        print(f"[ERR] Bark 返回非 200: {resp}", file=sys.stderr)
        return False
    return True


def main():
    if RESET:
        load_dedup()
        return

    # 1. 找候选卡（已学过的）
    note_ids = anki("findNotes", query=DECK_QUERY)
    if not note_ids:
        print("[INFO] 候选池为空（无已学卡），跳过", file=sys.stderr)
        return

    # 2. 当日去重
    pushed_today = load_dedup()
    available = [n for n in note_ids if n not in pushed_today]
    if not available:
        # 当日全部推过 → 重置后再抽，避免空推
        print(f"[INFO] 今日已轮一遍 ({len(pushed_today)} 张)，重置后继续", file=sys.stderr)
        pushed_today = set()
        available = note_ids

    # 3. 拉详情
    notes = anki("notesInfo", notes=available)

    # 4. 加权抽卡
    weights = [HIGH_FREQ_BOOST if "高频" in n.get("tags", []) else 1 for n in notes]
    chosen = random.choices(notes, weights=weights, k=1)[0]

    # 5. 提字段
    fields = chosen.get("fields", {})
    front_raw = fields.get("Front", {}).get("value", "")
    back_raw = fields.get("Back", {}).get("value", "")
    front = clean_html(front_raw)
    back = clean_html(back_raw)

    # 6. 取卡组简称作 subtitle
    cid = chosen.get("cards", [None])[0]
    subtitle = ""
    if cid:
        card_info = anki("cardsInfo", cards=[cid])
        if card_info:
            subtitle = deck_short_name(card_info[0].get("deckName", ""))

    # 7. 截短 + 拼装 body
    title = front[:TITLE_MAX]
    tags = chosen.get("tags", [])
    tag_line = "  ".join(f"#{t}" for t in tags if t in ("高频", "原文填空", "论述题", "名词解释"))
    body_parts = []
    if tag_line:
        body_parts.append(tag_line)
    body_parts.append("─── 先回想，再下拉 ───\n")
    body_parts.append(back)
    body = "\n".join(body_parts)[:BODY_MAX]

    nid = chosen.get("noteId")
    print(f"[CARD] note={nid} deck={subtitle} title={title!r}")

    if DRY_RUN:
        print("─── DRY RUN ───")
        print(f"subtitle: {subtitle}")
        print(f"title:    {title}")
        print(f"body:     {body}")
        return

    # 8. 推送
    if push_bark(title, body, subtitle):
        pushed_today.add(nid)
        save_dedup(pushed_today)
        print(f"[OK] 推送成功 (今日已推 {len(pushed_today)} 张)")
    else:
        sys.exit(4)


if __name__ == "__main__":
    main()
