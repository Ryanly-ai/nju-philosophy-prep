# Obsidian 配置指南

> vault 路径：`~/Desktop/哲学史/`（大 vault，覆盖原著 + 教材 + 备考规划）

---

## 一、必装插件（3 个）

打开 Obsidian → **设置（齿轮图标）** → **第三方插件** → 关掉"安全模式" → 点 **浏览** → 分别搜索并安装：

| 插件               | 作用                                                | 搜索关键词          |
| ---------------- | ------------------------------------------------- | -------------- |
| **Templater**    | 每日日志自动填充日期、D 编号、阶段                                | `Templater`    |
| **Obsidian Git** | 每 15-30 分钟自动 commit + push 到 GitHub，云端触发器就能读到最新日志 | `Obsidian Git` |
| **Calendar**     | 侧边栏显示日历，点日期直接跳到当天日志                               | `Calendar`     |

三个装完后都要**点一下"启用"**。

---

## 二、核心插件配置

### 2.1 Daily Notes（内置）

**设置 → 核心插件 → 日记** 开启，然后 **设置 → 日记**：

- **日期格式**：`YYYY-MM-DD`
- **新建日记的默认位置**：`备考规划/每日日志`
- **模板文件的位置**：`备考规划/每日日志/模板.md`

### 2.2 Templater

**设置 → Templater**：

- **Template folder location**：`备考规划/每日日志`
- **Trigger Templater on new file creation**：**开启** ✅
- **Folder Templates** → 点 "+ Add new" → Folder: `备考规划/每日日志`，Template: `备考规划/每日日志/模板`

这样：每次用 Daily Notes 快捷键建新日志 → Templater 自动把模板里的 `<% ... %>` 替换成今天的日期、D 编号、阶段。

### 2.3 Obsidian Git

**设置 → Obsidian Git**：

- **Vault backup interval (minutes)**：`15`（每 15 分钟自动同步）
- **Auto pull interval**：`15`
- **Commit message**：`vault: auto-sync {{date}}`
- **Pull updates on startup**：开启 ✅

✅ **已配置完成**：vault 根目录 `~/Desktop/哲学史/` 已经初始化为 git repo，tracking 远程 `Ryanly-ai/nju-philosophy-prep` 的 main 分支。

`.gitignore` 已排除：
- `.DS_Store` / `.obsidian/workspace*.json`（本机状态）
- `备考建议和历代真题/`（本地研究资料，不上传）

所以 Obsidian Git **无需额外配置 base path**，默认就能工作。

---

## 三、首次连接 GitHub（Obsidian Git 用）

macOS 下 Obsidian Git 靠系统的 git 命令行 + 已有的 GitHub 认证。你之前装了 `gh` CLI 且登录了 Ryanly-ai 账号——这已经足够，Obsidian Git 会自动用 `gh` 的凭据。

**验证方式**：Obsidian 里按 `Cmd+P` → 输入 `Obsidian Git: Create backup` → 回车。如果状态栏出现"commit & push successful"，就 OK。

---

## 四、日常使用流程

### 4.1 每天早上（收到触发器推送后）

1. 打开 Obsidian（vault 自动更新到最新——Obsidian Git 启动时 pull）
2. 侧边栏 Calendar 里点今天的日期 → 自动用模板创建 `YYYY-MM-DD.md`
3. 参照手机推送里的任务清单，填入"今日任务"栏
4. 开始学习

### 4.2 每完成一项

- 在 Obsidian 里勾选 checkbox、填完成情况
- 无需手动 commit—— Obsidian Git 每 15 分钟自动同步

### 4.3 每天晚上（收到晚间检视推送后）

1. 回到今日日志
2. 填写"完成情况 / 今日收获 / 疑点 / 金句摘录 / 自评"
3. 15 分钟后，云端触发器就能读到

### 4.4 读书笔记联动（Obsidian 的杀手功能）

读到关键概念时：

- 在日志里写 `今天读到 [[性善论]]` —— 双方括号会自动变成双链
- Obsidian 会在 `性善论.md` 页面（如果没有就自动创建）显示"反向链接"——所有提到过这个概念的日志、原著标注
- 复习时打开 `[[性善论]]` 页面 → 能看到：原著原文摘录 + 所有涉及到它的日志 + 所有 Anki 卡片草稿

建议建立的"MOC 主题页"（Map of Content）：
- `[[孔子]]` `[[孟子]]` `[[老子]]` `[[庄子]]` …
- `[[性善论]]` `[[仁政]]` `[[道论]]` `[[无为]]` …
- `[[真题高频考点]]`（反链会聚合所有碰到的高频点）

**不用一次建完**—— Obsidian 的双链是写到哪建到哪。

---

## 五、排错

### "Obsidian Git: failed to push"
- 检查是否 vault 有未解决冲突（Obsidian 右上角会显示）
- 手动跑一次：`cd ~/Desktop/哲学史/备考规划 && git pull --rebase && git push`

### "Templater 模板没替换，变量字符串还在"
- 检查 **Trigger Templater on new file creation** 是否开启
- 检查 Folder Templates 里的路径是否正确（不带 `.md` 后缀）

### "Calendar 插件不显示日期"
- 检查 Daily Notes 的日期格式是否严格等于 `YYYY-MM-DD`

---

## 六、可选增强（熟悉之后再装）

- **Dataview**：把所有日志的"专注度自评"做成表格或图表
- **Periodic Notes**：自动生成周报 / 月报框架
- **Admonition**：漂亮的笔记块（提示 / 警告 / 关键）
- **Excalidraw**：画思想图谱（比如"先秦诸子谱系图"）

这些装了会锦上添花，但**前面三个才是核心**。
