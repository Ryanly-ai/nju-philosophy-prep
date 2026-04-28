# 英语 Anki 词库 · 使用说明

## 📁 文件结构

```
Anki/
├── README.md             ← 本文件
├── 总词库.tsv             ← 累积主词库（每日追加，导一次就够）
└── Day{N}_YYYY-MM-DD.tsv ← 每日增量包（可选导入）
```

## 🎴 卡片字段

每张卡 3 个字段：
1. **Front**：英文单词
2. **Back**：HTML 富文本（音标 + 词性 + 中文 + 文中例句 + 中文翻译 + 真题频次）
3. **Tags**：空格分隔的标签

## 🏷️ 标签说明

| 标签 | 含义 |
|------|------|
| `Day1` `Day2` ... | 第几天学的 |
| `必背` | Phase 1 核心词池（800 词） |
| `支持词` | 用户每日标记的『不熟但非主背』词（不限大纲） |
| `高频` | 真题出现 ≥10 次 |
| `超高频` | 真题出现 ≥50 次 |
| `熟词僻义` | 含真题考点僻义（如 subject/address） |
| `错词` | 当日测验答错，加权重学 |
| `搭配` | 含固定搭配（如 peer review / in accord with） |
| `盲区` | 摸底标 ✓ 但审词标 ✗（误以为会的词） |

## 📥 首次导入步骤（Mac · Anki Desktop）

### 方案 A：导入主词库（推荐 · 一次到位）

1. 打开 Anki Desktop
2. 顶部菜单 **File → Import**
3. 选 `总词库.tsv`
4. **重要设置**：
   - **Type**: `Basic`（基础双面卡）
   - **Deck**: 新建一个 deck，命名为「考研英语 · Phase 1」
   - **Field separated by**: `Tab`
   - ✅ **Allow HTML in fields**（必勾，否则 HTML 标签直接显示）
   - **Field 1** → maps to `Front`
   - **Field 2** → maps to `Back`
   - **Field 3** → maps to `Tags`（如未自动识别，手动选 "Tags"）
5. 点 **Import** → 提示"已导入 30 张卡"

### 方案 B：每日增量（适合不想覆盖学习进度）

1. 同样 File → Import
2. 选当天的 `Day{N}_YYYY-MM-DD.tsv`
3. 设置同上，勾 **「Update existing notes」** 避免重复

## 🔁 推荐复习节奏

Anki 默认 SRS 算法已经合理。建议设置：
- **新卡每日上限**：30（每日 20 主背 + 10 支持词刚好）
- **复习上限**：200（防止复习累积爆炸）
- **简单 / 良好 / 困难** 按真实感觉打——别要面子

## 🎯 学习方法

每日打卡完成后再过 Anki 卡片：
1. 先看 Front 想中文 → 翻 Back
2. 朗读音标 + 例句（强烈建议配合 macOS 朗读 / Edge TTS）
3. **熟词僻义**和**错词**卡片**优先用『困难』**，加密复习节奏
4. **支持词**用『良好』即可，不必死磕

## 🛠️ 后续日常工作流

每日 Day N 完成后，Claude 自动：
1. 生成 `DayN_YYYY-MM-DD.tsv`
2. 追加到 `总词库.tsv`
3. 你重新导入 `总词库.tsv`（勾 Update existing notes）= 增量更新

或者更轻：直接导每日的增量文件即可。

## ⚠️ 常见问题

**Q: 导入后卡片显示 `<b>` `<br>` 等标签**
A: 没勾 "Allow HTML in fields"。删掉重导，勾上即可。

**Q: 已经导过一次，怎么追加新卡不重复？**
A: Import 时勾 "Update existing notes"。Anki 按 Front 字段去重。

**Q: 想用 EN→CN 和 CN→EN 双向卡？**
A: 导入时 Type 选 "Basic (and reversed card)" — 自动生成两面卡。但每日实际复习量翻倍，建议先单向。
