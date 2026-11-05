# acskill

这是我持续维护的 AI 工具库。每个工具叫一个 **Skill**，可以理解成给 AI 用的工作说明书。

目前有七个工具，按你要做的事选择即可：

| 你想做什么 | 工具 | 说明入口 |
| --- | --- | --- |
| 给知识库建立目录和管理规则 | 知识库初始化 · `acs-knowledge-governance-bootstrap` | [查看说明](skill/acs-knowledge-governance-bootstrap/README.md) |
| 把本地音视频整理成文字 | 音视频文字提取 · `acs-video-script-extractor` | [查看说明](skill/acs-video-script-extractor/README.md) |
| 用本人授权声音给文案配音 | 本人声音克隆配音 · `acs-voice-clone` | [查看说明](skill/acs-voice-clone/README.md) |
| 判断选题、开头与读者的关系 | 内容吸引力审核 · `acs-content-appeal-review` | [查看说明](skill/acs-content-appeal-review/README.md) |
| 审核文章或口播稿 | 个人文章与口播稿审核 · `acs-content-review` | [查看说明](skill/acs-content-review/README.md) |
| 把定稿做成公众号发布包 | 公众号定稿发布包 · `acs-wechat-publish-pack` | [查看说明](skill/acs-wechat-publish-pack/README.md) |
| 检索并整理公考培训行业消息 | 公考培训行业动态简报 · `acs-industry-brief` | [查看说明](skill/acs-industry-brief/README.md) |

**知识库初始化后，日常按库内规则工作。** 初始化工具把规则和检查工具放进知识库，并设计自有Skill的完整保存、索引与接手方式。以后查资料、入库和更新项目情况，让AI读取库内AGENTS.md即可；换Agent可复用已有内容，按需适配入口、依赖与权限。已有规则会优先沿用。

第一次使用，先看 **[新手入门](docs/新手入门.md)**，里面有各个工具的使用方法和可复制提示词。

## 怎么开始

把仓库链接和你的需求一起交给 AI：

```text
请阅读这个仓库：https://github.com/iamaresfive/acskill
我想做的是：【填写你的需求】。
请帮我选择合适的 Skill，检查当前工具和电脑环境是否支持，并指导我安装和使用。
第一次先查看现有资料，告诉我准备怎么做，等我确认后再修改。
```

AI 工具需要支持加载或明确读取 Skill、访问本地文件和执行相应命令。[新手入门](docs/新手入门.md#使用前准备)说明完整包保存、客户端引用和最小检查；安装 Skill 后，再分别检查知识库配置、转写模型或配音环境。音视频转写采用自动转写＋AI／人工复核，配音初始化复用已有本地环境。

## 工具分别做什么

### 1. 知识库初始化

适合从零建立知识库，或给已有知识库补齐管理规则。新库默认使用中文目录；已有库保留原目录和资料，先给你看具体方案，确认后再安装规则、模板和检查工具。

安装完成后，日常让 AI 读取库内 `AGENTS.md` 并按规则工作即可；需要调整管理规则时，再使用初始化工具。

[详细说明](skill/acs-knowledge-governance-bootstrap/README.md) · [快速开始](skill/acs-knowledge-governance-bootstrap/docs/quick-start.md)

### 2. 音视频文字提取

适合本地课程、访谈、会议和短视频文件。用两个本地模型转写并比较差异，有可见字幕时结合画面复核。可指定处理片段，也可按需交付校对逐字稿、还原整理稿和待确认疑点。

运行前需要准备好依赖和模型。转写过程离线，不会自动下载网络视频，也不会自动把结果写进知识库。

[详细说明](skill/acs-video-script-extractor/README.md) · [快速开始](skill/acs-video-script-extractor/docs/quick-start.md)

### 3. 本人声音克隆配音

在 Apple Silicon Mac 上，用本人明确授权的声音把文案合成为中文旁白。支持分段生成、断点复用、单段重做，以及本地 Whisper 文字核对。

本包不含声音样本或模型，须先准备本地环境与本人授权参考录音；不会自动上传声音或发布作品。

[详细说明](skill/acs-voice-clone/README.md) · [环境与初始化](skill/acs-voice-clone/references/runtime.md)

### 4–6. 内容创作工具

| 创作步骤 | Skill | 用途 |
| --- | --- | --- |
| 讨论主线、检查入口 | [acs-content-appeal-review](skill/acs-content-appeal-review/README.md) | 检查目标读者、阅读收获、继续关注与商业承接理由 |
| 审核修改 | [acs-content-review](skill/acs-content-review/README.md) | 核对事实、主线与逻辑，保留作者表达 |
| 定稿后制作 | [acs-wechat-publish-pack](skill/acs-wechat-publish-pack/README.md) | 制作可复制图文、封面和手机预览，运行包内检查 |

[完整流程与具体案例](docs/公众号创作流程与Skill.md)包含日常积累素材、提出观察、核对材料、起草和复盘，以及[飞书方法文档](https://qs4978dogu.feishu.cn/docx/QKNbdUiAWoPEp0xHZgKcv0VBnCc)的对应入口。这是现行工具的分工说明，不把后来沉淀的Skill说成历史文章当时全部调用过。

### 7. 公考培训行业动态简报

让AI检索行业公开信息、逐条读源，按监管与政策、市场与同业、网络舆情生成HTML和证据JSON。信息不足如实说明；不需要个人知识库或飞书连接，需要联网、文件及Python执行能力。

[详细说明与提示词](skill/acs-industry-brief/README.md) · [Agent生成的版式示例](skill/acs-industry-brief/examples/Agent生成的版式示例.html)

## 仓库目录

下面只展示主要入口，七个工具使用同一层级：

```text
acskill/
├── README.md                               # 总入口
├── docs/
│   └── 新手入门.md                         # 怎么选、怎么开始
└── skill/
    ├── acs-knowledge-governance-bootstrap/   # 知识库初始化
    ├── acs-video-script-extractor/           # 音视频文字提取
    ├── acs-voice-clone/                      # 本人声音克隆配音
    ├── acs-content-appeal-review/            # 内容吸引力审核
    ├── acs-content-review/                   # 个人文章与口播稿审核
    ├── acs-wechat-publish-pack/              # 公众号定稿发布包
    └── acs-industry-brief/                   # 公考培训行业动态简报
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

## 许可与商业授权

本项目中由维护者有权授权的原创 Skill 文档、提示词、说明材料和配套源代码，采用 [CC BY-NC 4.0](LICENSE) 许可证。

- 非商业性学习、研究及其他非商业用途，可按协议使用、复制和改编。
- 对外分享原文或修改版时，请注明作者与来源，保留许可声明及链接，并标明修改情况。
- 商业用途请联系维护者取得单独授权。
- 第三方内容及依赖遵循各自的许可证。

作者为 [iamaresfive](https://github.com/iamaresfive)，来源为本仓库。文档和代码的具体适用范围见[许可范围说明](NOTICE.md)，协议条件以[许可全文](LICENSE)为准。

商业授权可通过 [GitHub Issue](https://github.com/iamaresfive/acskill/issues/new) 联系，说明拟使用的 Skill 和商业用途。授权以双方另行确认的书面约定为准。
