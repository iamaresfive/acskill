# 制作与验收细则

## 账号要求和视觉参考

账号署名、品牌、栏目、封面尺寸、正文配图与作者卡以使用者已确认的要求为准。本包不带私人账号配置、作者卡、客户稿件或字体二进制。

可选视觉参考：白底、深蓝`#1a3a6b`、正文16px、约1.9倍行高、19px段距。它不是强制模板；历史样式也不能覆盖本次要求。需要准确尺寸时核对当前目标后台或用户规格，不把某个账号制作习惯写成平台规定。

## 图文安排和素材

- 封面准确表达主题，缩略图可辨，不必重复插入正文。
- 观点卡整理作者已有观点，不添加未经提供的数字和引语。
- 证据图保留上下文和来源，不能用生成式工具改写证据。
- 信息图用于比较、顺序或层次，不为凑数量加图。
- 每张正文插图有完整原文段落锚点与紧随图片的独立小字解说；图片中的标题、alt与侧栏说明不能代替图下解说。
- 固定作者卡按用户确认准源复制；不重新排字或拿候选稿替代。

字体选择有清晰许可的来源并随包附来源与许可记录；系统字体可显示不等于可分发字体文件。第三方图片、Logo、截图和AI生成图分别记录来源与使用范围，不承诺AI图天然无权利风险。不把私人素材随Skill公开。

## 输出目录

```text
公众号-短题-日期/
  00-标题摘要正文-复制用.txt
  01-发布复制页.html
  02-公众号正文.html
  定稿正文.txt
  图片/01-封面.png
  图片/02-主题图.png          # 仅在本次需要时生成
  手机预览.png
  手机首屏.png
  使用说明.md
  素材来源与许可.md
  package.json
  检查结果.json
```

用户要求的其他封面版本或许可文件放在同包，并列入`extras`。不打包缓存、会话、cookie、密钥或其他项目文件。

## 完整清单示例

下面是一张正文图、不带作者卡的示例；不是固定交付数量。路径均相对本包，正文HTML和复制页位于根目录，图片引用与清单路径一致。

```json
{
  "account": "我的公众号",
  "mode": "精修",
  "source": "定稿正文.txt",
  "article": "02-公众号正文.html",
  "copy_page": "01-发布复制页.html",
  "copy_text": "00-标题摘要正文-复制用.txt",
  "cover": "图片/01-封面.png",
  "body_images": ["图片/02-主题图.png"],
  "mobile_preview": "手机预览.png",
  "first_screen": "手机首屏.png",
  "instructions": "使用说明.md",
  "rights": "素材来源与许可.md",
  "extras": [],
  "summary_status": "建议",
  "platform_paste_verified": false,
  "layout": {
    "requirements": {
      "basis": "本次采用的方案：一张图解释文中结构，不需要作者卡。",
      "illustration_count": 1,
      "author_card_required": false
    },
    "illustrations": [
      {
        "image": "图片/02-主题图.png",
        "after_paragraph": "这里替换为定稿里对应的完整原段落。",
        "caption": "这里填写针对本图的简短解说。"
      }
    ]
  }
}
```

`requirements`在制作前按真实指令或已说明的方案填写，不能事后为了通过检查降低要求。`basis`写实际依据，不能照搬示例句。`illustration_count`是非负整数，`author_card_required`是布尔值。

有作者卡时增加`layout.author_card`，并在`body_images`最后列相同路径；运行时传准源文件。准源本身不会被打包，包内作者卡仍须可公开使用。无作者卡时不留隐藏作者卡字段或额外图片。

简洁模式通常使用`body_images: []`、`illustrations: []`、数量0、作者卡false，并填写真实模式依据。封面仍要交付。已确认的例外可用`layout.override`记录`user_instruction`及`illustration_count`／`author_card_required`变化，不能只有新数量没有依据。

## HTML结构

纯正文HTML和复制页均使用唯一`#article`。标题、摘要和操作提示在复制页的正文容器外；只复制正文容器。示例：

```html
<section id="article">
  <p data-approved="1">这里是定稿里对应的完整原段落。</p>
  <section>
    <img src="图片/02-主题图.png" alt="结构示意图">
    <p data-caption-for="图片/02-主题图.png">针对本图的简短解说。</p>
  </section>
  <p data-approved="1">下一段定稿正文。</p>
</section>
```

图注与对应img同容器并紧邻，不纳入锁稿标记。所有源段落及原有小标题要标记；新增导航、图注、工具栏不标。不得用标记筛选掩盖正文增删。作者卡在最后一段定稿后。

复制页用Clipboard API写`text/html`和`text/plain`，失败则提示手动选择正文复制，不能把选中宣称为复制成功。正文样式内联，不依赖复杂grid或外部CSS在公众号保真。本地路径或base64图可能被过滤，使用说明须提示粘贴后检查，并从图片目录在原位置手动上传。

## 自动检查

只需Python 3.9+标准库，无需联网，无额外Python依赖。从本Skill目录运行：

```bash
python3 scripts/check_pack.py /path/to/publishing-package
# 实际打开图片与手机预览完成检查后：
python3 scripts/check_pack.py /path/to/publishing-package --visual-reviewed
# 需要作者卡时，追加指向用户确认准源的参数：
python3 scripts/check_pack.py /path/to/publishing-package --approved-author-card /path/to/approved-card.png --visual-reviewed
# 仅明确需要ZIP时再加 --zip /path/to/new-package.zip
```

目录与准源均由当前使用者提供。ZIP用新文件名、不覆盖旧包；按清单打包，拒绝符号链接、隐藏文件和目录穿越。失败退出非零；报告含SHA-256与检查状态，图片签名不是完整解码验收。

人工验收声明由执行者负责，不盲加参数。自动检查不核对`copy_text`的标题摘要分隔格式、不验证字体许可和尺寸，不证明每个源段落都在正确位置，也不证明微信实际粘贴成功。人工须查看复制页全部正文和图文位置，核对封面尺寸、品牌、署名、末句、数字与标点。

## 运行回归检查

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
```

测试使用临时合成素材，覆盖正文、复制页、图数、图注、锚点、作者卡和文件边界；不包含任何私人作者卡，不代表真实成品视觉效果已验收。
