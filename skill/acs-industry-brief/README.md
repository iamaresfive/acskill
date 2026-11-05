# 公考培训行业动态简报

让AI检索公考培训行业公开信息，逐条核对来源、日期与数据口径，生成一份可以用浏览器打开的HTML简报。

## 能做什么

固定三节：**监管与政策、市场与同业、网络舆情**。每条区分事实、研判和口径提醒，并附来源链接。目标7—9条，可靠信息不足时少写并说明，不用旧闻或报名日程凑数。

交付两个文件：HTML简报和同批证据JSON。JSON记录本期输入、检索与来源，不是原网页完整快照。

## 第一次使用

把下面这段话交给你的AI：

```text
请读取 https://github.com/iamaresfive/acskill/tree/main/skill/acs-industry-brief
把acs-industry-brief完整包保存在我指定的工具目录，保留references、scripts、assets和agents。
先检查联网检索、读取来源、保存文件及Python 3.9以上执行能力，按当前客户端支持的方式安装或明确加载，不覆盖已有同名Skill。
准备好后按SKILL.md做一份今天的公考培训行业动态简报，交付可打开的HTML及同批证据JSON。
信息不足如实说明；没有历史简报就说明未做历史去重。先做一份，不创建定时任务，不代发。
```

AI需要具备联网搜索、实际读取来源、文件读写和运行Python 3.9及以上版本的能力。脚本只使用标准库；不需要个人知识库或飞书连接。不能操作文件与命令的纯聊天环境，无法直接完成本包安装和文件生成。

## 装好以后

```text
使用acs-industry-brief，做一份今天的公考培训行业动态简报，交付HTML和证据JSON。
```

HTML用浏览器打开；抽查关键来源和数字。需要每天自动运行时，先单次跑通，再按所用工具另行配置。

## 看版式

[Agent生成的版式示例](examples/Agent生成的版式示例.html)是已有成品的展示副本。下载HTML后用浏览器打开；示例只用于看排版，未完成逐条原文核验，不作为新闻依据或本Skill验收结果。正式生成时，仍须按包内证据规则逐条读源。

## 文件与检查

- [SKILL.md](SKILL.md)：AI执行入口。
- [采编与证据规则](references/editorial.md)：选编、来源与研判要求。
- [输入与交付格式](references/input-format.md)：本期JSON和字段说明。
- `scripts/brief.py`：离线排版及检查；`assets/style.css`：固定三节样式。
- `scripts/test_brief.py`：合成回归用例，不是新闻资料。

```sh
python3 scripts/brief.py render 本期输入.json --output-dir 本次成果目录
python3 scripts/brief.py check 本次成果目录/YYYY-MM-DD-公考培训行业动态简报.html --input 本期输入.json
```

版本v1.1支持独立安装位置，保护Skill包本身及按结构识别出的知识库，拒绝覆盖已有同名成品。13项离线回归与包结构校验通过；脚本通过不能证明消息真实或研判成立，仍需联网读源与人工审定。

本工具不自动外发、定时运行、发布或入库，不替代个人观点文章、单一机构经营建议或政治时政周报。

## 许可与商业授权

本 Skill 中由维护者有权授权的原创说明、提示词及配套源代码采用 [CC BY-NC 4.0](https://github.com/iamaresfive/acskill/blob/main/LICENSE) 许可。作者为 [iamaresfive](https://github.com/iamaresfive)，来源为 [acskill](https://github.com/iamaresfive/acskill)。具体适用范围见[许可范围说明](https://github.com/iamaresfive/acskill/blob/main/NOTICE.md)。

非商业用途可按协议使用。对外分享时请保留署名、来源和许可声明，并标明修改情况。商业授权可通过 [GitHub Issue](https://github.com/iamaresfive/acskill/issues/new) 联系维护者。
