# 个人文章与口播稿审核

核对事实、主线、逻辑和表达，保留作者的态度与说话位置。适合个人文章、评论、口播的审稿和按意见改稿。

当前公开版 `v1.6-public.1`。有改前改后两版时，可对照作者实际改动，判断哪些修改让观点更清楚、哪些改偏了。去AI味时按段落实际作用取舍。v1.6起会检查个案结论有没有被写成整个行业的规律；只要意见时默认按“总体判断、必须改、事实待核、可选建议”输出；标题和开头的吸引力交给内容吸引力审核。

## 怎么用

提供稿件、写作背景、目标受众及需要保留的立场；如果已在当前对话里说明，无需重填。需要改稿时直接说“按意见改一版”。

```text
请使用 $acs-content-review 审核下面的稿件。
保留我的中心判断和表达力度，指出事实待核、逻辑问题及值得保留的部分。
先给意见，不直接重写；没有实质问题就保留。
```

## 安装与能力要求

保存完整`acs-content-review/`文件夹，不能只复制SKILL.md；保留随包的references、agents，以及存在的scripts。按当前AI客户端支持的Skill目录安装或建立指向完整目录的入口；不支持自动发现时，让它明确读取[SKILL.md](SKILL.md)。已有同名工具先比较，不能直接覆盖。

只需能读取文件并按规则工作的AI工具；事实查询按实际可用联网工具进行。无需安装外部dbskill，也不自动组织多模型审稿。

## 与其他步骤怎么配合

查看[公众号创作流程与工具对应](https://github.com/iamaresfive/acskill/blob/main/docs/公众号创作流程与Skill.md)。按需要使用，不要求每篇依次跑完所有工具。

[给AI的执行规则](SKILL.md) · [仓库总入口](https://github.com/iamaresfive/acskill)

本目录是适合公开使用的版本：使用当前作者的目标、账号要求与输出路径，不依赖维护者的内部知识库。它不是文章效果保证，安装不代表已经完成审核、渲染或发表。

## 许可与商业授权

本 Skill 中由维护者有权授权的原创说明、提示词及配套源代码采用 [CC BY-NC 4.0](https://github.com/iamaresfive/acskill/blob/main/LICENSE) 许可。作者为 [iamaresfive](https://github.com/iamaresfive)，来源为 [acskill](https://github.com/iamaresfive/acskill)。具体适用范围见[许可范围说明](https://github.com/iamaresfive/acskill/blob/main/NOTICE.md)。

非商业用途可按协议使用。对外分享时请保留署名、来源和许可声明，并标明修改情况。商业授权可通过 [GitHub Issue](https://github.com/iamaresfive/acskill/issues/new) 联系维护者。
