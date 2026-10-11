# 运行环境与输入说明

仅初始化、迁移、故障恢复或自定义配置时读取。普通配音复用已有环境。

## 支持环境与前置条件

已验证 Apple Silicon、Python 3.12、MLX Audio 0.5.8、MLX 0.32.3，模型为 `mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit`。其他平台和版本未验证。

本包是离线配音工作流，不是自带模型的一键安装器。需要预先准备可运行上述模型的 Python 环境、完整本地模型，以及本人同意使用的参考音频。按用户授权从官方来源准备依赖；本包脚本不会自动安装、联网下载或上传声音。

## 固定位置

默认运行根目录为 `~/.local/share/acs-voice-clone/`。非默认位置使用 `voice_clone.py --runtime-root /本机运行目录 doctor`；该全局参数放在子命令前。

- `env/bin/python`：独立 Python 环境；仍依赖创建它的基础 Python，须保留该基础安装。
- `model/`：完整本地模型，体积约 3 GB，不随本包分发。
- `voices/self/`：参考 WAV、身份或代称、同意记录及参考文字；仅存本机，不提交到公共仓库。
- `runtime.json`：环境版本、模型来源及校验清单；普通检查核对模型元数据，`doctor --deep` 重新计算模型哈希。

声音 ID 可用 `--voice-id` 设置，后续通过 `doctor --voice ID` 或 `generate --voice ID` 选择。首次初始化不会继承发布者或其他人的授权。

如有知识库、原始资料或其他不可写目录，设置 `ACS_VOICE_PROTECTED_ROOTS`，macOS 下多个绝对路径用冒号分隔。初始化、生成和转写报告都拒绝写入这些目录；Skill 包自身默认受保护。输出和模型仍应放在独立目录，不能依赖脚本自动识别所有私人资料位置。

## 初始化或恢复

`bootstrap.py` 只复用本机已验证的 MLX 环境和模型，不联网。它用相同主次版本的基础 Python 新建 venv，再复制原环境 site-packages；完整复制并核验模型及参考音频。目标必须不存在，不覆盖已有安装。初始化须处于用户明确授权的搭建或恢复任务内。

参考录音须为 3 至 30 秒、单声道 24 kHz PCM16 WAV，单人说话、少噪声、无背景音乐；参考文字必须对应实际说出的内容。

```bash
/已验证环境/bin/python scripts/bootstrap.py \
  --reuse-env /已验证环境 \
  --model /已下载的Qwen3-TTS模型目录 \
  --reference /本人录音/reference.wav \
  --reference-text '参考录音的逐字内容' \
  --speaker '我的本地代称' \
  --voice-id self \
  --consent-note '本人于某日同意以该声音在本地合成此次文稿' \
  --authorized
```

`--authorized` 是执行声明，不是声音授权的证据。先核实实际同意，再如实填写记录；不能因参数可填写就替他人授权。

若初始化中断，保留目录并定位原因；不递归删除、不自动从第三方镜像下载。沙箱无法访问 Metal 时可通过宿主工具正常的审批流程执行，不降低系统安全设置。

## 输入与复用

文本按句切分为不超过 140 字符的段落；JSON 每段最多 300 字符，长句自行拆分。ID 仅英文、数字、下划线和连字符。JSON 可为字符串数组，或 `{"segments":[{"id":"s01","text":"原文","spoken_text":"读音处理后文字"}]}`。

默认 seed 42、temperature 0.7、top_p 0.9、max_tokens 1200。`--pause` 控制段间停顿（默认 0.3 秒）；输入、声音或参数改变须新建输出目录，避免错误复用。`--redo s02` 仅给指定段生成新种子和新文件，旧版本保留。

每个任务使用独立输出目录；同一运行目录的生成进程互斥，忙时直接返回。清单写入采用原子替换；异常中断已成功片段仍可复用。已有但未登记的非空输出目录拒绝写入，文件哈希异常也拒绝覆盖。

## 离线文字核对

`verify_voice.py` 需要已安装的 `faster-whisper` 和已缓存的 `medium` 模型。当前 Python 没有依赖时，可指定已有环境：

```bash
python3 scripts/verify_voice.py \
  --job /绝对路径/独立配音任务 \
  --python /Whisper环境/bin/python
```

脚本强制本地模型读取，不自动下载。可用 `--model large-v3` 复核疑点，前提是该模型也已缓存。重复运行仅在音频、输入和模型选项未变时复用结果。

- 退出码 0：归一化后的文字完全一致，标记 `machine_text_match`。
- 退出码 3：存在差异，标记 `needs_review`，需结合文稿和音频复核。
- 退出码 2：输入、依赖、音频或运行错误，不能宣称验收通过。

标点、数字、同音字和缩写可能产生误报。文字匹配不证明音色相似、语气自然，也不等于人工听验；发布使用前仍须试听并明确 AI 合成身份。

技术来源：[MLX Audio](https://github.com/Blaizzy/mlx-audio)、[Qwen3-TTS 模型](https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit)。实际环境以本机 `runtime.json` 为准，日常配音不自动升级。
