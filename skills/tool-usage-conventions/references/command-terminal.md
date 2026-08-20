# 命令与终端工具约定（Command & Terminal）

> 命令执行有两套工具：`Bash`（一次性）与 `terminal`（常驻/交互）。
> 选错的成本：Bash 里跑常驻服务会卡住等超时；terminal 里跑一次性命令会留在后台刷屏。

---

## T1 选择规则

| 场景 | 用哪个 |
|------|--------|
| 短且会自行结束的命令（列目录、搜索、构建、lint、格式化、git、装依赖） | **Bash**（同步等待，默认超时 120s，上限 3600s） |
| 耗时但会结束、需要等结果的任务（编译、测试、长安装） | **terminal(action="start", notify=true)** —— 等系统主动回调，**勿轮询** |
| 常驻服务（`npm run dev`、`python server.py` 等） | **terminal(action="start", notify=false)**，再配合 read/send/key/close |
| 驱动行式交互程序（git commit 编辑器、npm init、python REPL、ssh 密码） | **terminal** 的 start + send + key + read（Bash 做不到中途交互） |

## T2 Bash 超时建议

- 默认 120 秒；耗时命令用 `timeout` 参数调大；
- `./gradlew assembleDebug` → 1800 秒；
- `./gradlew assembleRelease` 或 R8/Proguard 全量优化 → 2400 秒；
- aarch64 模拟 x86_64 跑 Android 构建更慢 → 必要时给满 3600 秒。

## T3 terminal 会话纪律

**复用优先**：启动新常驻进程或执行交互式命令前，先 `terminal(action="read")`（不传 tab_id）列出现有终端；若有之前创建的活跃标签，直接用 `action="send"` **复用**，切忌反复 start 开一堆新窗口。

### action="start"
- 必填 `command`，可选 `title`、`notify`；
- 启动后挂起约 5 秒并流式捕获初始输出，返回 `{tab_id, running, output}`（过长时另有 output_truncated / output_path）；
- **notify=false（默认）**：常驻服务用。命令结束后 exec 默认 shell 保活标签，可继续 send/read；**不会在结束时回调**，需要结果时自己 read；
- **notify=true**：会自行结束、且你要等结果的任务用。start 返回后**不要再 sleep/read 轮询**——命令结束系统会自动注入 `<task-notification>`（含最后 10 行输出）并触发新一轮；仅当需要完整日志时再 `terminal(action="read", tab_id=...)`。notify=true 结束后标签不再活跃（不可 send），新任务重新 start。

### action="send"
- 向已有终端发送一行命令/输入（默认自动回车执行），随后像 start 一样等待约 5 秒显示新增输出；
- 必填 `tab_id`、`input`，可选 `submit`；
- 若终端已不再活跃，send 会被拒绝——改用 start 新建。

### action="key"
- 发送快捷键/控制字符。必填 `tab_id`、`key`；
- 支持：`ctrl+c`、`ctrl+d`、`ctrl+z`、`ctrl+l`、`ctrl+u`、`ctrl+w`、`esc`、`tab`、`enter`、`up`、`down`、`left`、`right`；
- 中断后台标签里正在跑的前台命令时**优先用 key="ctrl+c"**。

### action="read" / "close"
- `read`：按 tab_id 读取某终端当前输出（含后台命令实时日志）；超长按 output_path 规则回填 preview；省略 tab_id 则列出所有终端标签及状态；
- `close`：按 tab_id 关闭终端标签并终止其中进程；常驻任务不再需要时，**先 read 确认目标，再 close 清理**。

## T4 驱动交互式程序（Bash 做不到）

terminal 能驱动行式交互程序（git commit 编辑器、npm init 问答、python REPL、ssh 密码提示等）：

1. `start` 启动后停在输入提示处；
2. `send` 逐行发输入（默认自动回车）；
3. `key` 发 tab/enter/ctrl+c 等控制键；
4. `read` 查看当前输出判断状态。

Bash 一次性执行等命令结束，**无法中途交互**——遇到交互程序就用 terminal。

## T5 环境工具（Android 构建专用）

- `ensure_android_env`：aarch64/ARM64 容器一键准备 Android APK 构建环境（JDK 17 / cmdline-tools / sdkmanager / licenses / `~/.rcodecore/env.sh` / Build-Tools 二进制 qemu-x86_64 wrapper）。**每次构建 Android 项目前、或看到「AAPT2 架构不兼容 / Exec format error」时，优先调用本工具**，不要手动逐条 apk add / curl / 自己找 wrapper。参数全可选，幂等；
- `check_environment`：安装前后调用，确认 Java/Gradle/Android SDK/QEMU-x86-translator 状态是否 installed；
- `switch_container_arch`：在 arm64 原生（默认，最快）与 x86_64 QEMU 转译间无感切换。**需要 x86_64 工具链（aapt2/zipalign 等）时优先用本工具切到 x86_64 容器**，而不是只做单个 wrapper。

## T6 环境内置工具

环境已内置 `git`、`rg`（ripgrep）、`py/python`、`node`。需要时**优先直接通过 Bash 调用，不要先询问是否安装**。
