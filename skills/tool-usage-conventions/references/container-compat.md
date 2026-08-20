# 容器命令兼容性与执行纪律（Container Compatibility）

> 执行环境是 **Alpine Linux（BusyBox ash/awk/grep/nc/sed 等）**，不是 GNU/Linux。
> 写命令必须 **POSIX / BusyBox 兼容**，禁用 GNU 专属语法——否则命令解析即报错、重试又失败，白白消耗时间。

---

## C1 GNU → BusyBox 对照表（写命令前自查）

| GNU 写法 | BusyBox 正确写法 |
|----------|-----------------|
| `nc -q 1 host port`（GNU netcat「EOF 后等待」） | **不支持**。用 `nc -w 1 host port`，或改用 `wget -T 2 -O /dev/null URL` / `curl --connect-timeout 2 -s` |
| `grep -P` / `grep \d` / `grep \s` | 无 `-P`、不认 `\d\s`。用 `grep -E` + `[0-9]` / `[[:space:]]`，或 `LC_ALL=C grep '[^ -~]'` 做字节级非 ASCII 检测 |
| `awk '\x{4e00}'`（gawk Unicode 语法） | 不支持。用 `LC_ALL=C` 字节判断 |
| `date -d '...'`（GNU -d 解析） | 无 GNU -d 解析（`-d @epoch` 部分支持）。跨平台优先 `date +%s` / `date -u +%FT%TZ` |
| `head -n -N` / `tail -n +N` 负数写法 | 部分版本不支持。用 `awk`/`sed` 替代 |

> 也可用自检脚本 `scripts/busybox_lint.py` 对将要执行的命令做静态检查。

## C2 严禁无界循环

**禁止** `while true; do ...; done`、`while :`、`until false`、`for ((;;))` 这类**没有退出条件**的循环（尤其配合 nc/ping/curl/wget/重试时）——会无限刷屏、空耗 CPU。

需要等待/轮询时：
- **有限次数**（如 `for i in 1 2 3 4 5` / `seq`）+ `sleep` 间隔 + 明确退出条件；
- **在超时前结束**。

## C3 常驻终端 ≠ 一次性命令

- `terminal(action="start")` 常驻模式**没有超时**：notify=false 的常驻终端命令会一直运行直到手动停止，**只适合真正常驻的服务**（npm run dev、python server.py 等）；
- 一次性命令、探测、循环、构建等**会自行结束的任务一律用 Bash**（有超时强制终止）或 `terminal(action="start", notify=true)`（结束后自动回调）；
- 把循环/探测塞进常驻终端 = 停不下来的刷屏。

## C4 失败先修根因，不盲目重试

- 命令失败先读报错定位原因（如上面的 BusyBox 兼容问题）再修；
- 同一条命令**连续失败 2 次就换方法**或向用户说明，不要反复原样重试。
