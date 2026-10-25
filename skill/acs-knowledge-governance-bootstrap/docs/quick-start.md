# 快速开始

1. 让Agent读取本Skill，提供知识库路径和用途；已有库先只读识别权威规则、知识/来源目录和索引。
2. 确认需要的模块和主要维护者，以及自有Skill正式包、工具索引的位置。新库目录默认中文，已有库不改原名；Agent已有安装先比较，不自动搬迁。
3. 在库外生成方案，审阅新增/合并清单和候选全文。
4. 明确批准后执行安装，运行目标库独立检查，再人工核对语义。
5. 日常从库内AGENTS.md进入，按工具索引找到相关规范、脚本和自有Skill；只有治理升级再调用初始化Skill。

换Agent时，先让它读取库内AGENTS.md和工具索引，再适配运行入口、依赖与权限，做一次最小验证。规范和自有Skill的完整正式包留在库内，不用重新制作。具体见[工具与Skill管理规范](../references/tool-portability.md)。

命令（Python 3.10+）：

```bash
python3 scripts/bootstrap.py plan /absolute/vault --mode new --output /absolute/temp/plan
python3 scripts/bootstrap.py apply /absolute/temp/plan/plan.json --approved
python3 /absolute/vault/规范与工具/工具/治理检查.py
```

已有库在plan时使用 `--mode existing --config /absolute/temp/config.json`；[配置字段和冲突规则](../references/onboarding.md)。目标根目录须已存在；计划目录必须是库外新目录。--approved只表示已取得用户对该具体方案的批准。
