#!/usr/bin/env python3
"""
南大哲学考研备考·执行率计算器。

公式：
  执行率 = 100 - Σ(连跳惩罚 × 阶段权重) + Σ(回血) + Σ(里程碑奖励)
  - 起算日：2026-05-07（用户 2026-05-06 第二次清零，节奏不变重启）
  - 截止日：2026-12-20
  - 阶段权重：基础期 1.0 / 精读期 1.5 / 冲刺期 2.0 / 押题期 3.0
  - 连跳第 N 天扣分 = min(N, 5)
  - 回血：跳过后每连续完成 7 天 +1（每段最多 +5）
  - 里程碑：阶段一末 +5 / 阶段二末 +10 / 阶段三末 +15

判定一天是否"跳过"：
  1. 日志标题含"⏸ 跳过日"标记 → 跳过
  2. "专业课实际用时" 字段值为 0 或空 / 未填 → 跳过
  3. 日志文件不存在 → 跳过

用法：
  python3 计算执行率.py            # 输出 banner + 完整仪表盘到 stdout
  python3 计算执行率.py --banner   # 仅输出 banner（晨间触发器用）
  python3 计算执行率.py --dashboard # 生成 仪表盘.md
  python3 计算执行率.py --json     # JSON 格式（程序间用）
"""
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

# 路径锚定：本脚本位于 备考规划/统计/计算执行率.py，仓库根 = parent.parent.parent
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOG_DIR = REPO_ROOT / "备考规划" / "每日日志"
DASHBOARD_PATH = REPO_ROOT / "备考规划" / "统计" / "执行率仪表盘.md"

START_DATE = date(2026, 5, 7)
END_DATE = date(2026, 12, 20)

PHASES = [
    (date(2026, 4, 18), date(2026, 5, 31), "通史基础", 1.0),
    (date(2026, 6, 1), date(2026, 10, 15), "经典精读", 1.5),
    (date(2026, 10, 16), date(2026, 11, 30), "冲刺真题", 2.0),
    (date(2026, 12, 1), date(2026, 12, 20), "押题预测", 3.0),
]
PHASE_END_BONUS = {
    date(2026, 5, 31): 5,
    date(2026, 10, 15): 10,
    date(2026, 11, 30): 15,
}


def phase_for(d):
    for start, end, name, weight in PHASES:
        if start <= d <= end:
            return name, weight
    return None, 1.0


def log_path_for(d):
    return LOG_DIR / d.strftime("%Y-%m") / f"{d.isoformat()}.md"


def is_skipped(log_path):
    if not log_path.exists():
        return True
    content = log_path.read_text(encoding="utf-8")
    if "⏸ 跳过日" in content or "⏸ 调整规划日" in content:
        return True
    # 找「专业课实际用时」后面同一行（≤30 字符内）的第一个连续数字。
    # 容忍各种格式：`90 分钟` / `_90_ 分钟`（Markdown 斜体）/ `90` / `80 分钟（备注）` 等。
    # 限定 [^\n] 避免跨行匹配到下一字段（如「读到」）。
    m = re.search(r"专业课实际用时[^\n]{0,30}?(\d+)", content)
    if not m:
        return True
    return int(m.group(1)) == 0


def grade(score):
    if score >= 95:
        return "S", "⭐⭐⭐⭐⭐", "神级，南大稳了"
    if score >= 85:
        return "A", "⭐⭐⭐⭐", "强势上岸"
    if score >= 70:
        return "B", "⭐⭐⭐", "有戏，不能松"
    if score >= 55:
        return "C", "⭐⭐", "危险，要找回节奏"
    return "D", "⭐", "警报，需要重大调整"


def compute(today=None):
    today = today or date.today()
    last_eval = min(today - timedelta(days=1), END_DATE)

    base_result = {
        "score": 100.0,
        "as_of": today.isoformat(),
        "days_to_exam": max(0, (END_DATE - today).days),
        "days_evaluated": 0,
        "days_completed": 0,
        "days_skipped": 0,
        "completed_streak": 0,
        "skipped_segments": [],
        "complete_segments": [],
        "milestones_earned": [],
        "recovery_total": 0.0,
        "penalty_total": 0.0,
        "started": today >= START_DATE,
    }

    if last_eval < START_DATE:
        level, emoji, text = grade(100)
        base_result.update({"level": level, "level_emoji": emoji, "level_text": text})
        return base_result

    # 扫描 START_DATE..last_eval 每一天
    days = []
    cur = START_DATE
    while cur <= last_eval:
        skipped = is_skipped(log_path_for(cur))
        _, weight = phase_for(cur)
        days.append({"date": cur, "skipped": skipped, "weight": weight})
        cur += timedelta(days=1)

    # 算跳过段
    score = 100.0
    skipped_segments = []
    i = 0
    while i < len(days):
        if days[i]["skipped"]:
            j = i
            while j < len(days) and days[j]["skipped"]:
                j += 1
            penalty = 0.0
            for k, dd in enumerate(days[i:j], start=1):
                penalty += min(k, 5) * dd["weight"]
            score -= penalty
            skipped_segments.append({
                "start": days[i]["date"].isoformat(),
                "end": days[j - 1]["date"].isoformat(),
                "length": j - i,
                "penalty": round(penalty, 2),
            })
            i = j
        else:
            i += 1

    # 算完成段（用于回血）
    complete_segments = []
    seg_start = None
    for idx, d in enumerate(days):
        if not d["skipped"]:
            if seg_start is None:
                seg_start = idx
        else:
            if seg_start is not None:
                complete_segments.append((seg_start, idx - seg_start))
                seg_start = None
    if seg_start is not None:
        complete_segments.append((seg_start, len(days) - seg_start))

    recovery_total = 0.0
    complete_segs_info = []
    for seg_start_idx, seg_len in complete_segments:
        # 第一段（idx=0）= 从开局就完成，不算"恢复"，零回血
        if seg_start_idx == 0:
            complete_segs_info.append({
                "start": days[seg_start_idx]["date"].isoformat(),
                "length": seg_len,
                "recovery": 0.0,
                "type": "起步段",
            })
            continue
        recovery = min(seg_len // 7, 5)
        score += recovery
        recovery_total += recovery
        complete_segs_info.append({
            "start": days[seg_start_idx]["date"].isoformat(),
            "length": seg_len,
            "recovery": recovery,
            "type": "恢复段",
        })

    # 里程碑
    milestones_earned = []
    for m_date, bonus in PHASE_END_BONUS.items():
        if last_eval >= m_date:
            if not is_skipped(log_path_for(m_date)):
                score += bonus
                milestones_earned.append({"date": m_date.isoformat(), "bonus": bonus})

    score = max(0.0, score)
    level, emoji, text = grade(score)

    # 当前连续完成天数
    streak = 0
    for d in reversed(days):
        if not d["skipped"]:
            streak += 1
        else:
            break

    base_result.update({
        "score": round(score, 1),
        "level": level,
        "level_emoji": emoji,
        "level_text": text,
        "days_evaluated": len(days),
        "days_completed": sum(1 for d in days if not d["skipped"]),
        "days_skipped": sum(1 for d in days if d["skipped"]),
        "completed_streak": streak,
        "skipped_segments": skipped_segments,
        "complete_segments": complete_segs_info,
        "milestones_earned": milestones_earned,
        "recovery_total": round(recovery_total, 2),
        "penalty_total": round(sum(s["penalty"] for s in skipped_segments), 2),
    })
    return base_result


def render_banner(s):
    if not s["started"]:
        return (
            f"📊 **执行率：100 分** ⭐⭐⭐⭐⭐ **S 级** · 起算日 {START_DATE.isoformat()}\n"
            f"📅 距离考试 {s['days_to_exam']} 天 · 计算尚未启动 · 明天起每天打卡决定胜率"
        )
    parts = [
        f"📊 **执行率：{s['score']} 分** {s['level_emoji']} **{s['level']} 级**（{s['level_text']}）",
        f"📅 已评估 {s['days_evaluated']} 天 · 完成 {s['days_completed']} · 跳过 {s['days_skipped']} · "
        f"连续完成 **{s['completed_streak']}** 天 · 距考试 {s['days_to_exam']} 天",
    ]
    return "\n".join(parts)


def render_dashboard(s):
    L = []
    L.append("# 📊 执行率仪表盘\n\n")
    L.append(f"> 自动生成 · 数据截止 **{s['as_of']}**\n")
    L.append(f"> 起算日：**{START_DATE.isoformat()}** · 截止：**{END_DATE.isoformat()}** · 距考试 **{s['days_to_exam']}** 天\n\n")
    L.append("---\n\n")

    if not s["started"]:
        L.append("## ⏳ 计算尚未开始\n\n")
        L.append(f"起算日是 **{START_DATE.isoformat()}**。明天起，每天打卡 = 维持分数；跳过 = 扣分。\n\n")
        L.append("起步执行率：**100 分** ⭐⭐⭐⭐⭐ **S 级**\n\n")
    else:
        L.append("## 当前状态\n\n")
        L.append(f"### 🎯 执行率：**{s['score']}** 分\n")
        L.append(f"### {s['level_emoji']} **{s['level']} 级** · {s['level_text']}\n\n")
        L.append(f"| 指标 | 值 |\n|---|---|\n")
        L.append(f"| 已评估天数 | {s['days_evaluated']} |\n")
        L.append(f"| 完成 / 跳过 | {s['days_completed']} / {s['days_skipped']} |\n")
        L.append(f"| 当前连续完成 | **{s['completed_streak']}** 天 |\n")
        L.append(f"| 累计扣分 | -{s['penalty_total']} |\n")
        L.append(f"| 累计回血 | +{s['recovery_total']} |\n")
        L.append(f"| 距考试 | {s['days_to_exam']} 天 |\n\n")

        if s["skipped_segments"]:
            L.append("## 跳过记录\n\n")
            L.append("| 起 | 终 | 天数 | 扣分 |\n|---|---|:---:|:---:|\n")
            for seg in s["skipped_segments"]:
                L.append(f"| {seg['start']} | {seg['end']} | {seg['length']} | -{seg['penalty']} |\n")
            L.append("\n")
        else:
            L.append("## 跳过记录\n\n零跳过 ✨ 完美\n\n")

        if s["milestones_earned"]:
            L.append("## 里程碑奖励\n\n")
            for m in s["milestones_earned"]:
                L.append(f"- {m['date']} 完成阶段 +{m['bonus']}\n")
            L.append("\n")

    L.append("## 等级表\n\n")
    L.append("| 分数 | 等级 | 文案 |\n|:---:|:---:|---|\n")
    L.append("| 95+ | S ⭐⭐⭐⭐⭐ | 神级，南大稳了 |\n")
    L.append("| 85-94 | A ⭐⭐⭐⭐ | 强势上岸 |\n")
    L.append("| 70-84 | B ⭐⭐⭐ | 有戏，不能松 |\n")
    L.append("| 55-69 | C ⭐⭐ | 危险，要找回节奏 |\n")
    L.append("| <55 | D ⭐ | 警报，需要重大调整 |\n\n")

    L.append("## 计算公式\n\n")
    L.append("```\n")
    L.append("执行率 = 100 - Σ(连跳惩罚 × 阶段权重) + Σ(回血) + Σ(里程碑奖励)\n\n")
    L.append("连跳第 N 天扣分 = min(N, 5)\n")
    L.append("阶段权重：基础期 1.0 / 精读期 1.5 / 冲刺期 2.0 / 押题期 3.0\n")
    L.append("回血：跳过后每连续完成 7 天 +1（每段最多 +5）\n")
    L.append("里程碑：阶段一末 +5 / 阶段二末 +10 / 阶段三末 +15\n")
    L.append("```\n\n")

    L.append("> 本仪表盘由 `备考规划/统计/计算执行率.py` 自动生成。每天早上 08:00 晨间触发器会重新计算并更新此文件。\n")
    return "".join(L)


def main():
    args = set(sys.argv[1:])
    s = compute()

    if "--json" in args:
        print(json.dumps(s, ensure_ascii=False, indent=2, default=str))
        return

    if "--banner" in args:
        print(render_banner(s))
        return

    if "--dashboard" in args:
        DASHBOARD_PATH.parent.mkdir(parents=True, exist_ok=True)
        DASHBOARD_PATH.write_text(render_dashboard(s), encoding="utf-8")
        print(f"仪表盘已写入：{DASHBOARD_PATH}")
        return

    # 默认：打印 banner + 仪表盘到 stdout
    print(render_banner(s))
    print()
    print(render_dashboard(s))


if __name__ == "__main__":
    main()
