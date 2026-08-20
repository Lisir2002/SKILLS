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
├── skills/<skill-name>/         # 技能源码（SKILL.md + README + scripts/ + assets/）
├── packages/<skill-name>.zip    # 每个技能一个压缩包
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

## 技能索引

| 技能包 | 版本 | 说明 | 状态 |
|--------|------|------|------|
| （待添加） | - | 由用户逐个确认后发布 | 规划中 |

> 每个技能完成、确认、打包后，在此登记，并在 `CHANGELOG.md` 中记录。

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