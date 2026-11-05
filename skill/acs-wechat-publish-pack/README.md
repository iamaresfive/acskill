# 公众号定稿发布包

把已经确认的文章制作成可复制的富文本、封面与必要配图、手机预览和来源清单。支持精修与简洁模式，ZIP按需生成。

## 怎么用

提供定稿、目标账号要求、封面尺寸或可核对的发布目标、必要素材与输出位置。要沿用旧风格时提供实际成品；需要固定作者卡时提供确认过的准源文件。

```text
请使用 $acs-wechat-publish-pack，把这份已定稿正文做成公众号发布包。
采用简洁模式，保留正文自然段，封面单独交付；账号要求和尺寸按我提供的资料。
输出到我指定的新目录，检查正文一致和手机效果，不自动发表。
```

## 安装与能力要求

保存完整`acs-wechat-publish-pack/`文件夹，不能只复制SKILL.md；保留随包的references、agents，以及存在的scripts。按当前AI客户端支持的Skill目录安装或建立指向完整目录的入口；不支持自动发现时，让它明确读取[SKILL.md](SKILL.md)。已有同名工具先比较，不能直接覆盖。

检查脚本使用Python 3.9+标准库。实际制作还需要能生成HTML、读取本地文件并渲染手机预览的工具；插画生成、图片处理与字体另按本次需求准备。本包不带生图API、浏览器、字体或作者卡，也不会自动安装大体积依赖。

## 与其他步骤怎么配合

查看[公众号创作流程与工具对应](../../docs/公众号创作流程与Skill.md)。按需要使用，不要求每篇依次跑完所有工具。

[给AI的执行规则](SKILL.md) · [仓库总入口](../../README.md)

本目录是适合公开使用的版本：使用当前作者的目标、账号要求与输出路径，不依赖维护者的内部知识库。它不是文章效果保证，安装不代表已经完成审核、渲染或发表。

[清单格式、检查命令与验收边界](references/production.md)。本版作者卡准源通过`--approved-author-card`显式传入，不从私人知识库读取。

## 许可与商业授权

本 Skill 中由维护者有权授权的原创说明、提示词及配套源代码采用 [CC BY-NC 4.0](https://github.com/iamaresfive/acskill/blob/main/LICENSE) 许可。作者为 [iamaresfive](https://github.com/iamaresfive)，来源为 [acskill](https://github.com/iamaresfive/acskill)。具体适用范围见[许可范围说明](https://github.com/iamaresfive/acskill/blob/main/NOTICE.md)。

非商业用途可按协议使用。对外分享时请保留署名、来源和许可声明，并标明修改情况。商业授权可通过 [GitHub Issue](https://github.com/iamaresfive/acskill/issues/new) 联系维护者。
