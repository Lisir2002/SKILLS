# SKILLS 技能库（AI Skill Repository）

本仓库用于维护一套**高质量、可复用、标准化**的 AI 技能（Skill）集合。每一个技能都是一个完整的、符合统一规范的可安装技能包。

> 统一规范见 → [docs/SKILL-AGENTS.md](docs/SKILL-AGENTS.md)

---

## 什么是派生 Skill？

Skill 是一种可被 AI 智能体（Trae / Claude 等）加载执行的结构化指令包，由 `SKILL.md` 定义触发条件与执行流程，可按需附带脚本与资源。本仓库对每个技能做**强化设计**后，统一打包为 zip 发布。

---

## 仓库结构

```
SKILLS/
├── README.md                    # 本文档
├── docs/
│   ├── SKILL-AGENTS.md          # 技能设计与打包规范
│   ├── SKILL-TEMPLATE.md        # SKILL.md 推荐模板
│   └── DOC-WRITING-GUIDE.md     # 各类型文档规范写法
├── scripts/                     # 仓库级工具（校验器 + evals 运行器）
│   ├── validate_skills.py       # 技能自动化校验器
│   └── run_evals.py             # evals 运行器
├── skills/<skill-name>/         # 技能源码（SKILL.md + README + scripts/ + evals/ + assets/）
├── packages/<skill-name>.zip    # 每个技能一个压缩包
├── .github/workflows/           # CI：push 自动校验 + evals
└── CHANGELOG.md                 # 变更记录
```

---

## 如何安装 / 使用技能

1. 下载对应技能的压缩包 `packages/<skill-name>.zip`；
2. 解压后得到 `skills/<skill-name>/` 目录：
   - 放到 AI 工具的 skills 目录（如 `.trae/skills/<skill-name>/`）；
   - 或按工具的 Skill 安装流程导入；
3. 在对话中触发该技能的描述场景即可自动调用。

---

## 技能索引（分类导航）

| 分类 | 技能 | 版本 | 说明 | 状态 |
|------|------|------|------|------|
| ✍️ 写作与内容 | [de-ai-flavor](skills/de-ai-flavor/) | 0.1.0 | 去 AI 味：改写 AI 生成的中文文本更自然（Voice→Tells→Audit 三遍式 + 扫描脚本） | 已发布 |
| 🎬 媒体解析 | [media-parser](skills/media-parser/) | 0.1.0 | 多平台媒体解析：抖音/B站/快手/小红书/微博/YouTube 等 20+ 平台 → 无水印视频/图集/封面/标题/作者 | 已发布 |
| 🛡️ AI 行为治理 | [ai-rules](skills/ai-rules/) | 0.1.0 | 规范 AI 做事的规矩：三层宪法（底线+方法论+任务专属）+ 生成/确认/合规/复盘四脚本 | 已发布 |
| 🛠️ 工具与环境 | [tool-usage-conventions](skills/tool-usage-conventions/) | 0.1.0 | 工具使用约定：文件/命令/容器兼容/路径/Android 构建 SOP + BusyBox 兼容自检器 | 已发布 |
| 📊 数据可视化 | [visualization](skills/visualization/) | 0.7.0 | 可视化：Mermaid 图谱（11 图种）/ 离线 SVG 图表（8 图型，色盲安全配色）/ 表格 / HTML 报告（chart+columns 看板）+ 四个纯标准库脚本 | 已发布 |
| 💡 创新思维 | [creative-mind](skills/creative-mind/) | 0.1.0 | 通用创新引擎：破解模式坍缩，跳出固化思想造新东西——破固化→发散(12+技法)→收敛→验新四步 + 发散脚手架/固化度检测两脚本 | 已发布 |

> 每个技能完成、确认、打包后，在此登记，并在 `CHANGELOG.md` 中记录。

---

## 质量保障

仓库级工具保证所有技能符合 [SKILL-AGENTS.md](docs/SKILL-AGENTS.md) 规范：

```bash
python3 scripts/validate_skills.py            # 技能包静态校验（§7 清单）
python3 scripts/run_evals.py                  # evals 回归（触发路由 / 质量 / 冒烟）
```

每个技能自带 `evals/evals.json` 触发与质量用例；push 到 main 时由 GitHub Actions 自动执行上述两项检查。

---

## 贡献 / 提交流程

1. 提出技能需求；
2. 联网调研同类最佳实践，强化设计；
3. 按规范编写完整技能包（含 SKILL.md、脚本、说明、资源）；
4. 用户审核拍板；
5. 打包 `packages/<skill-name>.zip` 并推送。

---

## License

仅供学习与协作使用。技能包内容请遵循各技能的说明文件。