---
name: "tool-usage-conventions"
description: "Use whenever the user asks to read/edit/create/search project files, run build/install/test commands, or package an Android APK: enforces tool-usage conventions for this environment — readFile before stating file facts, editFile exact-match batch edits, viewImage fallback, writeFile/sendFile, Bash vs terminal choice with notify semantics, BusyBox-compatible commands (busybox_lint.py, no unbounded loops), path conventions, and the Android aarch64 build SOP (ensure_android_env / check_environment / switch_container_arch). Also when the user says 工具使用约定 / 文件操作 / 构建打包. Not for writing content, media parsing, or behavior rule generation."
---

# Tool Usage Conventions（工具使用约定 / 文件管理约束）

本技能约束 AI **在本环境下如何正确调用工具**：文件操作、命令执行、容器兼容、路径约定、Android 构建。重点是编码模型"会做错"的环境特有知识——BusyBox 语法、output_truncated 截断处理、aarch64 构建 SOP、工具选择纪律。

## Purpose / 用途

- 消除"把工具调用写成文本"、"不先读就下结论"、"在 BusyBox 上写 GNU 语法"、"反复原样重试"等高频错误；
- 提供**确定性的工具选择规则**（Bash vs terminal、readFile vs editFile vs writeFile），减少 AI 自由发挥；
- 保证 Android APK 构建走通（含失效方案禁令，防止 AI 自作主张发明不可行路径）。

## When to Use / 何时使用

- 用户要求**读取/编辑/新建/搜索**项目文件；
- 用户要求**运行**构建、安装、测试、格式化、git 等命令；
- 用户要求**打包 Android APK**，或出现 `AAPT2 架构不兼容 / Exec format error`；
- 用户提到 **工具使用约定 / 文件操作 / 构建打包 / BusyBox** 等环境约定话题；
- 即将执行 shell 命令前（用 `scripts/busybox_lint.py` 自检兼容性）。

## When NOT to Use / 反触发

- 纯内容创作（写作、润色——那是 de-ai-flavor 的职责）；
- 媒体解析（那是 media-parser 的职责）；
- AI 行为规矩体系（那是 ai-rules 的职责）。

## Workflow / 工作流程（工具选择决策树）

### 1. 要动文件 → 先读再改

- 陈述任何文件事实前，先 `readFile`（[file-tools.md](references/file-tools.md) F1）；
- 局部小改 → `editFile`（old_string 逐字精确匹配、多处合并一次调用、原子生效）；
- 新建/整文件重写 → `writeFile`（重写前先 readFile）；
- 看本地图片 → `viewImage`（原生识图 → 识图模型 → `MODEL_VISION_UNSUPPORTED`）；
- 发文件给用户 → `sendFile`。

### 2. 要执行命令 → 按选择规则定工具

- 短且会自行结束 → **Bash**（默认超时 120s，必要时 `timeout` 调大）；
- 耗时但会结束、要等结果 → **terminal(action="start", notify=true)**（等系统回调，勿轮询）；
- 常驻服务 → **terminal(action="start", notify=false)**，配合 read/send/key/close；
- 交互式程序（git commit 编辑器、python REPL、ssh 密码）→ **terminal** 的 start+send+key+read。
- 执行前可用 `python3 scripts/busybox_lint.py --cmd "<命令>"` 自检 BusyBox 兼容性。

### 3. 写命令 → 过 BusyBox 兼容纪律

- 对照 GNU→BusyBox 表自查（[container-compat.md](references/container-compat.md) C1）：`nc -q`、`grep -P`/`\d\s`、`awk \x{}`、`date -d`、`head/tail 负数`；
- **严禁无界循环**（`while true` / `for ((;;))` 等）；需要轮询用有限次数 + sleep + 退出条件；
- 失败先修根因，同命令连败 2 次换方法（C4）。

### 4. 构建 Android APK → 走 SOP

- 按 [android-build-sop.md](references/android-build-sop.md) 严格顺序：
  1. `ensure_android_env()`（一次性，幂等）；
  2. 构建前自检（gradlew / settings / local.properties 的 `sdk.dir=/root/android-sdk`）；
  3. 构建（Bash timeout=1800/2400/3600 或 terminal notify=true，加 `--no-daemon -x lint -x test --stacktrace`）；
  4. 报错排障表逐项对照；
  5. 提前说明性能预期（qemu 慢 8~20 倍），有 GitHub 优先建议 Actions 云端构建。

### 5. 协作/记忆/网络 → 按约定调用

- 需要用户决策 → `askUserQuestion`（有默认值就别问）；
- 记录规律/偏好/项目约定 → `memory(action="save")`，更新用 `edit` 局部改；
- 复杂任务 → `todo(items=[...])`（每次提交完整列表）；
- 时效信息/最新资料 → `websearch`；抓页面 → `webfetch`；共享浏览器 → `browser`。

## Output Spec / 输出规范

- 文件操作：改动前后关键内容可对比；editFile 整批原子成功或整体回滚；
- 命令执行：给出真实输出摘要；超长按 `output_path` 分段读，不重复执行；
- 构建：给成功产物路径 + 关键日志尾部；失败给根因 + 排障动作；
- 任何"完成/有效"声明附证据（测试输出、构建产物、页面截图）。

## Failure Modes / 失败模式

- **不先读就改**：用 writeFile 覆盖已有文件 / 凭记忆改内容 → 强制"先 readFile 再改"；
- **把工具调用写成文本**：贴代码块假装执行 → 直接调用工具；
- **BusyBox 语法报错**：`grep -P` / `awk \x{}` / `date -d` / `head -n -N` 解析即错 → 用 busybox_lint.py 自检；
- **无界循环刷屏**：`while true` + curl 重试 → 有限次数 + 退出条件；
- **常驻服务卡 Bash**：把 `npm run dev` 塞进 Bash 等超时 → 用 terminal notify=false；
- **构建不走 SOP**：手动 apk add / 降级 AGP / 换单个 aapt2 → 一律 `ensure_android_env()`；
- **截断就重跑**：output_truncated 后重复执行同一命令 → 用 readFile 读 output_path。

## Dependencies / 依赖

- 环境工具：`ensure_android_env` / `check_environment` / `switch_container_arch`（Android 构建专用，可选）；
- 内置工具：`git`、`rg`、`py/python`、`node`（直接 Bash 调用，勿询问安装）；
- 自检脚本：`scripts/busybox_lint.py`（纯 Python 标准库，离线）。

## References / Scripts

- 工具调用总则：[references/tool-discipline.md](references/tool-discipline.md)（直接调用/并行/output_truncated）
- 文件工具约定：[references/file-tools.md](references/file-tools.md)
- 命令与终端约定：[references/command-terminal.md](references/command-terminal.md)
- 容器兼容与执行纪律：[references/container-compat.md](references/container-compat.md)
- 路径约定：[references/paths.md](references/paths.md)
- 协作/记忆/网络工具：[references/collaboration-tools.md](references/collaboration-tools.md)
- Android 构建 SOP：[references/android-build-sop.md](references/android-build-sop.md)
- 自检脚本：[scripts/busybox_lint.py](scripts/busybox_lint.py)

## Examples / 示例

**例 1：先读后改（正确）**
```
1. readFile("~/workspace/src/Main.kt")      # 先拿原文
2. editFile("~/workspace/src/Main.kt", edits=[{old_string: "...", new_string: "..."}])  # 精确匹配局部改
```
错误示范：不读文件，直接 writeFile 整文件重写。

**例 2：BusyBox 兼容自检**
```bash
python3 scripts/busybox_lint.py --cmd 'grep -P "\\d+" data.txt'
# → 发现 1 个问题: grep-perl-regex → 改用 grep -E '^[0-9]+' data.txt
```

**例 3：截断处理（正确）**
```
Bash 构建输出 output_truncated=true, output_path=~/.rcodecore/tool-output/xxx.log
→ readFile(output_path, start_line=1) 分段查看，不再重跑构建
```

**例 4：Android 构建走 SOP**
```
1. ensure_android_env()                      # 一次性
2. check_environment()                       # 确认 installed
3. editFile(local.properties, sdk.dir=/root/android-sdk)   # 若为空
4. Bash("./gradlew assembleDebug -x lint --no-daemon --stacktrace", timeout=1800)
```
