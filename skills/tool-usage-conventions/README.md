# tool-usage-conventions · 工具使用约定（文件管理约束）

> 约束 AI 在本环境下如何正确调用工具：文件操作、命令执行、BusyBox 兼容、路径约定、Android APK 构建。
> 一句话：**工具当工具用，不写成文本；先读后改、精确匹配；BusyBox 语法自检；构建走 SOP。**

## 这是什么

一个"环境工具使用约定"技能，重点编码模型**会做错**的环境特有知识：

- **文件工具纪律**：readFile 先读后说/后改、editFile 精确匹配批量编辑、viewImage 识图回退、writeFile/sendFile 边界；
- **命令执行纪律**：Bash vs terminal 怎么选、notify 语义、怎么驱动交互式程序；
- **容器兼容纪律**：Alpine/BusyBox 下禁用 GNU 专属语法、严禁无界循环、失败先修根因；
- **路径约定**：`~/workspace`、`~/.rcodecore`、宿主私有目录；
- **Android APK 构建 SOP**：aarch64 手机上从零出包的完整流程 + 失效方案禁令；
- **协作/记忆/网络工具**：askUserQuestion / switchMode / memory / todo / websearch / webfetch / browser。

## 安装与使用

技能包解压即用。目录结构：

```
tool-usage-conventions/
├── SKILL.md                     # 技能入口（模型加载）
├── README.md                    # 本文件
├── references/
│   ├── tool-discipline.md       # 工具调用总则（直接调用/并行/截断处理）
│   ├── file-tools.md            # 文件工具约定（readFile/editFile/writeFile/viewImage/sendFile）
│   ├── command-terminal.md      # Bash vs terminal / notify / 交互式程序 / 环境工具
│   ├── container-compat.md      # BusyBox↔GNU 对照 / 禁无界循环
│   ├── paths.md                 # 路径约定
│   ├── collaboration-tools.md   # 用户交互 / memory / todo / 网络 / 浏览器
│   └── android-build-sop.md     # Android APK 构建标准作业流程
└── scripts/
    └── busybox_lint.py          # BusyBox 命令兼容性自检器
```

## 快速上手

### 1. 文件操作纪律（最常用）

- 陈述文件事实前 **先 readFile**；
- 局部小改 **用 editFile**（old_string 逐字精确匹配，多处合并一次调用）；
- 新建/整文件重写 **用 writeFile**（重写前先 readFile）；
- 看图片用 **viewImage**，发文件用 **sendFile**。

### 2. BusyBox 命令自检

```bash
python3 scripts/busybox_lint.py --cmd 'grep -P "\\d+" data.txt'
python3 scripts/busybox_lint.py --file build.sh
```

发现的问题按提示修正（对照 `references/container-compat.md` 的 GNU→BusyBox 表）。

### 3. 命令工具选择

| 场景 | 工具 |
|------|------|
| 短且会结束 | Bash |
| 耗时但会结束 | terminal(action="start", notify=true) |
| 常驻服务 | terminal(action="start", notify=false) |
| 交互式程序 | terminal(start+send+key+read) |

### 4. Android APK 构建（aarch64 手机）

严格按 [references/android-build-sop.md](references/android-build-sop.md)：

1. `ensure_android_env()` 一次性环境准备；
2. 自检 gradlew / settings / local.properties；
3. 构建（`./gradlew assembleDebug -x lint --no-daemon --stacktrace`，Bash timeout=1800）；
4. 报错对照排障表。

## 失效方案（严禁）

- 降级 AGP 7.0 禁用 AAPT2 ❌
- Docker x86_64 镜像 ❌
- 手动替换单个 aapt2 为 aarch64 版 ❌
- 不装环境直接 gradlew ❌

## 与其它技能的关系

- 环境底座：适用于任何在本环境运行的技能，作为工具调用约束；
- 与 ai-rules（行为规矩）、de-ai-flavor（写作）、media-parser（解析）互补，互不冲突。

## 设计依据

- 本技能内容源自环境工具使用约定（用户提供），整理为 Agent Skills 规范格式；
- 渐进式披露：SKILL.md 承载核心纪律，长文档按需加载（references 一层深引用）；
- 确定性优先：工具选择、命令兼容、构建流程均落实为可执行规则而非散文。

## 限制

- `busybox_lint.py` 为静态检查（正则匹配），无法覆盖全部语义问题（如管道里的 `\d` 经过复杂拼接），关键命令仍建议先人工过一遍对照表；
- 环境工具（ensure_android_env 等）为宿主内置，技能仅约定调用方式，不包含其实现。
