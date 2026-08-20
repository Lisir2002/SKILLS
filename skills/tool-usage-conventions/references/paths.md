# 路径约定（Path Conventions）

> 本环境是容器（PRoot 隔离），路径规则与普通桌面环境不同，写路径前先看本节。

---

## P1 项目根目录

- 项目根目录固定为容器内路径 **`~/workspace`**；
- 你只看得到、也只需使用容器内路径；
- 项目文件用 `~/workspace/...`（如 `~/workspace/src/Main.kt`）或**相对路径**（如 `src/Main.kt`，相对 `~/workspace`）。

## P2 容器系统文件

- `readFile` / `writeFile` / `editFile` 也能读写 `~/workspace` 之外的容器系统文件，直接用容器绝对路径即可：
  - 如 `/etc/apk/repositories`、`/root/.bashrc`、`/usr/local/bin/...`

## P3 AI 配置目录

- AI 配置目录固定为 **`~/.rcodecore`**，可用文件工具或 Bash 直接访问；
- 它映射到 Android 宿主私有目录 `filesDir/rcodecore`，**不在 rootfs 内，容器重装不会清空**。

## P4 宿主私有目录（Android root 权限）

用户若拥有 Android root 权限，可绕过 DocumentsProvider 直接从宿主访问 App 私有目录：

- `/data/data/com.R.codecore/files/`（部分系统显示为 `/data/user/0/com.R.codecore/files/`）
- 其中 `projects/` 是本地工作区根，`rcodecore/` 对应容器内 `~/.rcodecore`。

## P5 工作目录与输出日志

- **Bash 的当前目录已经是 `~/workspace`**，相对路径都基于该项目根目录解析；
- `~/.rcodecore/tool-output/...` 是**工具完整输出日志目录**，可直接用 readFile 分段读取（对应 output_truncated 的 output_path）。

## P6 常用路径速查

| 路径 | 用途 |
|------|------|
| `~/workspace` | 项目根目录 |
| `src/...` | 相对项目根 |
| `/etc/apk/repositories` | Alpine 软件源 |
| `~/.rcodecore` | AI 配置目录（持久，容器重装不清） |
| `~/.rcodecore/env.sh` | 环境变量脚本（登录自动 source） |
| `~/.rcodecore/tool-output/` | 工具完整输出日志 |
| `/data/data/com.R.codecore/files/` | Android 宿主私有目录（需 root） |
