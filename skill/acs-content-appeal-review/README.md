# 内容吸引力审核

检查标题与开头、目标读者、阅读收获，以及继续关注或咨询的理由。适合开稿前选切入点，也适合检查成稿有没有把亮点呈现出来。

当前公开版 `v1.5-public.1`。开稿或改结构时，有自己账号的数据就先看同类内容表现，再参考同平台、同类型的内容，检查正文有没有兑现开头的承诺。v1.5起会检查细分赛道以外的同行能否看出与自己的关系，并明确只在你要求时改稿。

## 怎么用

提供选题或稿件、目标读者、平台和希望读者采取的动作。已有背景不用重复填写；商业化目标按你的实际要求评估，不默认人人都要卖产品。

```text
请使用 $acs-content-appeal-review，按我这篇内容的目标读者检查吸引力。
先说最有效的地方，再提最多三个优先修改点；引用原句，不预测流量，不擅自换受众或重写全文。
```

## 安装与能力要求

保存完整`acs-content-appeal-review/`文件夹，不能只复制SKILL.md；保留随包的references、agents，以及存在的scripts。按当前AI客户端支持的Skill目录安装或建立指向完整目录的入口；不支持自动发现时，让它明确读取[SKILL.md](SKILL.md)。已有同名工具先比较，不能直接覆盖。

只需能读取文件并按规则工作的AI工具；事实查询按实际可用联网工具进行。无需安装外部dbskill，也不自动组织多模型审稿。

## 与其他步骤怎么配合

查看[公众号创作流程与工具对应](https://github.com/iamaresfive/acskill/blob/main/docs/公众号创作流程与Skill.md)。按需要使用，不要求每篇依次跑完所有工具。

[给AI的执行规则](SKILL.md) · [仓库总入口](https://github.com/iamaresfive/acskill)

本目录是适合公开使用的版本：使用当前作者的目标、账号要求与输出路径，不依赖维护者的内部知识库。它不是文章效果保证，安装不代表已经完成审核、渲染或发表。

[审核尺度与外部方法来源](references/calibration.md)保留对dbskill的参考说明；本包不包含或重新授权第三方Skill。

## 许可与商业授权

本 Skill 中由维护者有权授权的原创说明、提示词及配套源代码采用 [CC BY-NC 4.0](https://github.com/iamaresfive/acskill/blob/main/LICENSE) 许可。作者为 [iamaresfive](https://github.com/iamaresfive)，来源为 [acskill](https://github.com/iamaresfive/acskill)。具体适用范围见[许可范围说明](https://github.com/iamaresfive/acskill/blob/main/NOTICE.md)。

非商业用途可按协议使用。对外分享时请保留署名、来源和许可声明，并标明修改情况。商业授权可通过 [GitHub Issue](https://github.com/iamaresfive/acskill/issues/new) 联系维护者。
