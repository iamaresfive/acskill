# 本人声音克隆配音

**Skill 名称：`acs-voice-clone`**

把文案合成为本人授权声音的中文旁白，在 Apple Silicon Mac 上离线运行。适合口播、动画旁白和短句试听；不包含动画制作、视频转写、上传或发布。

## 能做什么

- TXT 自动分段，或用 JSON 指定每段原文和实际读音文字。
- 生成独立片段与完整 WAV，按实际音频长度输出段落时间轴。
- 已完成片段校验后复用，中断后继续；只重做有问题的一段，旧片段保留。
- 用本地 Whisper 筛查漏字、错读和重复，报告差异位置。

## 先准备什么

本仓库只提供代码和说明，**不包含任何人的声音、授权记录或模型**。下载本工具不代表获得使用别人声音的权限。首次使用须准备本人的明确同意、参考录音和对应文字；不要上传声音配置、生成清单或音频到公共仓库。

已验证 Apple Silicon + Python 3.12，使用 MLX Audio 与 Qwen3-TTS 1.7B Base 8bit。需要先有可用的本地环境和模型；初始化脚本只复用已有环境，不自动联网安装。其他平台和版本未验证。

按 [运行环境与输入说明](references/runtime.md)完成初始化，再让 AI 使用 [SKILL.md](SKILL.md)。

## 怎么调用

```text
请使用 $acs-voice-clone，用我已登记并授权的声音给下面文案配音。
先做短句试听，再生成各段；检查有没有漏字或错读。
输出放到我指定的独立任务目录，不上传、不发布。
```

初始化完成后，也可以直接运行：

```bash
python3 scripts/voice_clone.py doctor
python3 scripts/voice_clone.py generate \
  --input /绝对路径/文稿.txt \
  --output-dir /绝对路径/独立配音任务 \
  --authorized
python3 scripts/verify_voice.py \
  --job /绝对路径/独立配音任务 \
  --python /Whisper环境/bin/python
```

`--authorized` 只能在确有授权时使用。相同命令可复用完成的片段；追加 `--redo s02` 可重做该段。文稿或参数改变时新建输出目录。

## 输出与边界

主要交付是 `旁白.wav`。`takes/` 保存各段，`timeline.json` 是段落时间轴，不是逐词字幕；`manifest.json` 记录声音、输入和模型指纹，属于本机工作资料，不随代码分发。

`quality.json` 检查波形，`asr-review.json` 筛查文字差异。机器文字匹配不代表声音自然或与本人完全一致。交付和使用时注明“本人授权的 AI 合成”，发布前自行试听，不用于冒充或身份验证。

## 测试

在已安装 NumPy 的 Python 环境运行，不需要加载配音模型：

```bash
python3 -B -m unittest discover -s tests -v
```

测试覆盖分段、授权拒绝、目录保护、片段指纹、复用、局部重做参数、波形和文字差异等；单元测试不替代真实配音和试听。
