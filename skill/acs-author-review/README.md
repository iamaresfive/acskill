# 作者内容审核

审核公众号文章、口播和短帖，检查事实、主线、逻辑、表达和本篇商业任务。先判断观点是否成立，再区分硬伤、表达过满或不清、可选优化，保留作者的判断与口吻。

当前版本：`v1.0`。这是 `0.1.1-draft` 经同主题稿件校准后按维护者确认启用的正式版本；尚未完成跨模型和多题材验证，不保证传播或成交效果。

## 怎么用

把稿件和这次要做的事交给AI。已有背景无需重填；明确只要意见、改一段还是改全文。作者的真实经历、立场和产品资料以本次提供的内容为准。

```text
请读取 https://github.com/iamaresfive/acskill/tree/main/skill/acs-author-review
使用作者内容审核 Skill 审核下面的稿件。
先判断主线是否成立，区分硬伤、表达过满或不清、可选优化。
保留我的立场和表达力度，先给意见，不直接重写全文。
【粘贴稿件与必要背景】
```

已经安装的客户端可直接说：`使用 $acs-author-review 审核这篇稿件`。要修改时说明范围；要承担销售任务时提供真实产品及入口，不能由AI补造承诺。

## 安装与能力要求

保存完整 `acs-author-review/` 文件夹，保留 `SKILL.md`、`references/` 和 `agents/`。按当前客户端支持的方式加载；不支持自动发现时，让AI明确读取[执行规则](SKILL.md)。遇到已有配置先比较，再按用户确认切换。

只需能读取稿件与随包文件的AI；核对时效事实需要可用的搜索工具或原始资料。此包不需要第三方Skill依赖，不自动安排多模型审核、发布或入库。

## 旧版迁移

本包统一替代旧 `acs-content-review` 和 `acs-content-appeal-review` 的当前使用入口。更新时移除这两份旧包的自动发现入口，按需留作不可自动加载的历史备份，避免三套规则同时触发。

新版不是旧两份功能的逐项合并：它以作者的本篇任务为中心，不承担专门的流量预测或完整选题研究。已有案例和来源说明属于旧版历史，不因为下架而改写；Git历史仍可追溯。

稿件定稿后可使用[公众号发布包](https://github.com/iamaresfive/acskill/blob/main/skill/acs-wechat-publish-pack/README.md)，完整分工见[创作流程](https://github.com/iamaresfive/acskill/blob/main/docs/公众号创作流程与Skill.md)。

## 许可与商业授权

本Skill中由维护者有权授权的原创说明、提示词及配套文件采用 [CC BY-NC 4.0](https://github.com/iamaresfive/acskill/blob/main/LICENSE) 许可。作者为 [iamaresfive](https://github.com/iamaresfive)，来源为 [acskill](https://github.com/iamaresfive/acskill)。具体范围见[许可范围说明](https://github.com/iamaresfive/acskill/blob/main/NOTICE.md)。

非商业用途可按协议使用；分享时保留署名、来源、许可并标明修改。商业授权可通过 [GitHub Issue](https://github.com/iamaresfive/acskill/issues/new) 联系维护者。
