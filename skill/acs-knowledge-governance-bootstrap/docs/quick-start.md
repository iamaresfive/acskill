# 快速开始

1. 让Agent读取本Skill，提供知识库路径和用途；已有库先只读识别权威规则、知识/来源目录和索引。
2. 通过对话确认需要的模块与本批负责人，以及自有Skill正式包、工具索引的位置。新库目录默认中文，已有库不改原名；Agent已有安装先比较，不自动搬迁。
3. 分别核对知识库管理、工作文件夹、工作产出、中转站规则。在库外生成方案；有冲突先说明原规则、整改建议及影响，准备可审阅候选，让用户选择并明确同意。
4. 明确批准后执行安装，运行目标库独立检查，再人工核对语义；按[接手验证](../references/onboarding.md#接手验证)确认目标Agent实际读取和遵循规则，无法访问其环境则明确待验证。
5. 日常从库内AGENTS.md进入，按工具索引找到相关规范、脚本和自有Skill；只有治理升级再调用初始化Skill。

换Agent时，先让它读取库内AGENTS.md和工具索引，再适配运行入口、依赖与权限，做一次最小验证。规范和自有Skill的完整正式包留在库内，不用重新制作。具体见[工具与Skill管理规范](../references/tool-portability.md)。

命令（Python 3.10+）：

```bash
python3 scripts/bootstrap.py plan /absolute/vault --mode new --output /absolute/temp/plan
python3 scripts/bootstrap.py apply /absolute/temp/plan/plan.json --approved
python3 /absolute/vault/规范与工具/工具/治理检查.py
```

已有库在plan时使用 `--mode existing --config /absolute/temp/config.json`；[配置字段和冲突规则](../references/onboarding.md)。目标根目录须已存在；计划目录必须是库外新目录。--approved只表示已取得用户对该具体方案的批准。

## 可复制提示词

```text
请读取这个Skill，先检查我的已有知识库和规则。通过对话引导我选择模块，不重复问已提供的信息。工作文件分类和交接中转站分别让我选择是否启用；分类可沿用现有、采用推荐或自定义。请生成配置和具体差异方案，经我确认再应用。保留既有资料和自定义规则，不自动迁移旧文件、改其他Agent配置、入库或清理中转站。
```

工作文件分类与中转站默认关闭，具体位置仅在启用后确认。Agent填写配置，用户不用写JSON。
