# acskill

这是我持续维护的 AI 工具库。每个工具叫一个 **Skill**，可以理解成给 AI 用的工作说明书。

目前有四个工具，按你要做的事选择即可：

| 你想做什么 | 工具 | 说明入口 |
| --- | --- | --- |
| 给知识库建立目录和管理规则 | 知识库初始化 · `acs-knowledge-governance-bootstrap` | [查看说明](skill/acs-knowledge-governance-bootstrap/README.md) |
| 日常查资料、入库、更新项目情况 | 第二大脑管理器 · `acs-second-brain-manager` | [查看说明](skill/acs-second-brain-manager/README.md) |
| 把本地音视频整理成文字 | 音视频文字提取 · `acs-video-script-extractor` | [查看说明](skill/acs-video-script-extractor/README.md) |
| 用本人授权声音给文案配音 | 本人声音克隆配音 · `acs-voice-clone` | [查看说明](skill/acs-voice-clone/README.md) |

**两个知识库工具可以独立使用，不用都装。** 初始化工具把规则和检查工具放进你的知识库，之后 AI 可以直接按库内规则工作；管理器用于持续查询、入库和更新。已有规则会优先沿用。

第一次使用，先看 **[新手入门](docs/新手入门.md)**，里面有四个工具各自的使用方法和可复制提示词。

## 怎么开始

把仓库链接和你的需求一起交给 AI：

```text
请阅读这个仓库：https://github.com/iamaresfive/acskill
我想做的是：【填写你的需求】。
请帮我选择合适的 Skill，检查当前工具和电脑环境是否支持，并指导我安装和使用。
第一次先查看现有资料，告诉我准备怎么做，等我确认后再修改。
```

AI 工具需要支持加载 Skill、访问本地文件和执行相应命令。音视频转写还需要本地模型和依赖，先让 AI 检查环境。

## 四个工具分别做什么

### 1. 知识库初始化

适合从零建立知识库，或给已有知识库补齐管理规则。新库默认使用中文目录；已有库保留原目录和资料，先给你看具体方案，确认后再安装规则、模板和检查工具。

安装完成后，日常让 AI 读取库内 `AGENTS.md` 并按规则工作即可；需要调整管理规则时，再使用初始化工具。

[详细说明](skill/acs-knowledge-governance-bootstrap/README.md) · [快速开始](skill/acs-knowledge-governance-bootstrap/docs/quick-start.md)

### 2. 第二大脑管理器

适合长期维护本地 Markdown / Obsidian 知识库：查以前的资料、整理新材料、更新项目状态、核对冲突和检查断链。保留原始来源，让当前结论能查到依据。

第一次接管已有库先只读了解结构。已在使用管理器的人可以继续使用，无需为了初始化再安装另一个工具。

[详细说明](skill/acs-second-brain-manager/README.md) · [快速开始](skill/acs-second-brain-manager/docs/quick-start.md) · [专项记忆使用说明](skill/acs-second-brain-manager/docs/project-memory-guide.md)

### 3. 音视频文字提取

适合本地课程、访谈、会议和短视频文件。用两个本地模型转写并比较差异，有可见字幕时结合画面复核，输出校对逐字稿、还原整理稿和待确认疑点。

运行前需要准备好依赖和模型。转写过程离线，不会自动下载网络视频，也不会自动把结果写进知识库。

[详细说明](skill/acs-video-script-extractor/README.md) · [快速开始](skill/acs-video-script-extractor/docs/quick-start.md)

### 4. 本人声音克隆配音

在 Apple Silicon Mac 上，用本人明确授权的声音把文案合成为中文旁白。支持分段生成、断点复用、单段重做，以及本地 Whisper 文字核对。

本包不含声音样本或模型，须先准备本地环境与本人授权参考录音；不会自动上传声音或发布作品。

[详细说明](skill/acs-voice-clone/README.md) · [环境与初始化](skill/acs-voice-clone/references/runtime.md)

## 仓库目录

下面只展示主要入口，四个工具使用同一层级：

```text
acskill/
├── README.md                               # 总入口
├── docs/
│   └── 新手入门.md                         # 怎么选、怎么开始
└── skill/
    ├── acs-knowledge-governance-bootstrap/   # 知识库初始化
    ├── acs-second-brain-manager/             # 第二大脑管理器
    ├── acs-video-script-extractor/           # 音视频文字提取
    └── acs-voice-clone/                      # 本人声音克隆配音
```

每个工具里的文件分工：

| 文件或目录 | 用途 |
| --- | --- |
| `README.md` | 给你看的工具介绍 |
| `SKILL.md` | 给 AI 执行的具体规则 |
| `docs/` | 快速开始、案例和常见问题 |
| `references/` | 执行时需要的详细规范 |
| `scripts/` | 运行工具 |
| `tests/` | 验证工具行为的测试 |
| `agents/` | Agent 接口配置 |

部分工具还有 `templates/`，用于提供可复用模板。第一次使用只需从[新手入门](docs/新手入门.md)开始，其他文件按需要阅读。


## 公开发布与隐私

贡献或发布前请阅读[公开发布检查](docs/公开发布检查.md)，检查个人信息、内部规则、凭据及 Git 提交身份。
