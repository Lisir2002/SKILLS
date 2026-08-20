# Android APK 构建标准作业流程（aarch64 手机）

> 背景：当前容器常跑在 aarch64 Android 手机上（PRoot 隔离）。Android SDK 官方 Build-Tools 只提供 x86_64 二进制，直接调用 aapt2/zipalign/split-select 等会出现 `Exec format error`、或被上层包装成「AAPT2 架构不兼容」这类报错。容器已内置 QEMU 用户态转译链路 + 一键环境工具，按下述步骤走即可构建成功。

---

## 0. 严禁再使用的失效方案（不要再自己发明）

- ❌ 不要降级 Android Gradle Plugin 到 7.0「禁用 AAPT2」——该开关已被永久移除，AGP 7/8 强制使用 AAPT2；
- ❌ 不要用 Docker x86_64 镜像——手机没有 Docker daemon，也不是 x86 CPU，此路物理上不存在；
- ❌ 不要只「手动替换单一 aapt2 为 aarch64 社区版」——Build-Tools 还有 zipalign/split-select/aidl/dexdump/… 共 10+ 个 x86 ELF，补一个会在下一步炸；
- ❌ 不要一上来就直接 `./gradlew assemble*`——没装 JDK/SDK 会先炸，浪费 10+ 分钟。

## 1. 一次性环境准备（只跑一次）

调用 `ensure_android_env()`（不传参数，按默认值）。它完成：

1. `apk add openjdk17`（缺 JDK 时自动装）；
2. 下载 Google cmdline-tools → 安装到 `$ANDROID_HOME/cmdline-tools/latest`；
3. `(yes || true) | sdkmanager --licenses` 接受许可；
4. `sdkmanager "platforms;android-34" "build-tools;34.0.0" "platform-tools"`；
5. **关键**：aarch64 架构下，自动确保 qemu-user-static 装好并运行 `rcodecore-wrap-android-buildtools`，把 Build-Tools 下所有 x86_64 ELF 转成 `qemu-x86_64 <original_bin> "$@"` 的同名 shell wrapper，从根上消除 `Exec format error`；
6. 把 `JAVA_HOME` / `ANDROID_HOME` / `PATH` 追加写入 `~/.rcodecore/env.sh`，后续 Bash / terminal 登录自动 source。

（可选）之后再调用 `check_environment()` 确认 Java / Gradle / Android SDK 状态为 installed。

## 2. 构建前快速自检

- `cd ~/workspace`，确认项目根目录里有 `gradlew` + `settings.gradle*` + `build.gradle*` + `local.properties`（或 local.properties 中 `sdk.dir` 指向 `$ANDROID_HOME`）；
- 若 local.properties 存在但 `sdk.dir` 为空/不对，用 editFile 改成：
  ```
  sdk.dir=/root/android-sdk
  ```
  （ensure_android_env 默认把 SDK 放在这个路径，和 `$ANDROID_HOME` 一致。）

## 3. 构建命令与超时（Bash 或 terminal 二选一）

优先 **terminal(action="start", notify=true)**：
```
terminal(action="start", notify=true, command="cd ~/workspace && ./gradlew assembleDebug -x lint --no-daemon --stacktrace 2>&1", title="gradlew assembleDebug")
```
或 **Bash**：
```
Bash(command="./gradlew assembleDebug -x lint --no-daemon --stacktrace", timeout=1800)
```

**Release 构建（开 R8）**：给 `timeout=2400` 或 `3600`（qemu 模拟下慢得多，一定要给足）。

**常见参数**：
- `--no-daemon`：手机内存有限，每次构建后立即释放 JVM 更稳；
- `-x lint -x test`：绕开 QEMU 模拟 + KVM 缺失导致的 Gradle daemon/测试进程不稳；
- `--stacktrace`：构建失败能把真正报错打印出来。

## 4. 报错排障

| 报错 | 处理 |
|------|------|
| `aapt2: Exec format error` / `zipalign: not found` | 回到第 1 步重新 `ensure_android_env()`，通常 wrapper 脚本已更新重跑即可 |
| `java.lang.OutOfMemoryError: GC overhead limit exceeded` / `Java heap space` | 用 Bash 在 `~/workspace/gradle.properties` 补/改为 `org.gradle.jvmargs=-Xmx1024m -XX:MaxMetaspaceSize=512m`（手机内存受限时别开 2GB） |
| `sdkmanager: command not found` / `ANDROID_HOME not set` | `check_environment(components=["Android SDK"])` 确认是否 installed；缺失就 `ensure_android_env()` 再来一轮 |
| `read time out` / `Connection reset` 下载大依赖网络抖动 | 同一命令多跑几次；或给 Bash 加 timeout |

## 5. 性能预期（提前对用户说明）

- qemu-x86_64 用户态翻译：aapt2 + R8 为纯 CPU 密集型，速度比 x86 真机**慢 8~20 倍**；
- 空白 Demo App debug 包：15~25 分钟；release 包带 R8：~40 分钟起步；中大型项目可能 60 分钟（Bash timeout 上限 3600 秒）；
- 以上仅为"能在手机内出 APK"的**兜底路径**。若用户有 GitHub/开发机访问能力，强烈推荐用 Git 推送 + GitHub Actions（仓库已内置 `.github/workflows/android-release.yml`）做云端构建——速度快、省手机电与发热。
