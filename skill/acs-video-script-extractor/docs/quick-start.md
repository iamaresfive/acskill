# Quick Start

这是 `acs-video-script-extractor` 的最短启动路径：自动转写＋AI／人工复核。下面的命令可交给 AI 执行，不需要自己逐条敲。

## 1. 准备环境

确认本机已有：

```bash
python --version
ffmpeg -version
ffprobe -version
```

当前 Python 需要能导入：

```bash
python -c "import faster_whisper; print('ok')"
```

默认还需要本地已经缓存 `large-v3` 与 `medium` 两个模型。Skill 运行时不会自动下载。

还没有环境或模型时，把这段交给 AI，先做准备：

```text
请先检查本机Python、faster-whisper、FFmpeg／ffprobe和两种模型的实际位置。
缺少时按faster-whisper官方说明列出依赖与兼容模型来源，先说明下载和存储需求，在我授权范围内准备。
确认large-v3和medium都能离线读取；模型应是faster-whisper兼容格式，不能只看见同名文件夹就认定可用。
准备完成后，先用一小段无隐私音频验证，再处理完整文件；不要覆盖原音视频。
```

模型缓存位置随环境而异，让 AI 回报实际路径；使用同一 Python 环境检查和运行。来源见 [faster-whisper 官方项目](https://github.com/SYSTRAN/faster-whisper)。

如果 `faster-whisper` 在另一个 Python 环境：

```bash
export ACS_TRANSCRIBE_PYTHON="/path/to/python"
```

FFmpeg 不在 PATH 时：

```bash
export ACS_FFMPEG="/path/to/ffmpeg"
export ACS_FFPROBE="/path/to/ffprobe"
```

## 2. 建立独立输出目录

优先使用用户指定或当前任务已约定的位置。为新的转写批次使用独立输出目录，例如 `/path/to/task/output`。下面的命令用 `/path/to/output` 代指该目录，预检和转写共用它。

### 只处理指定片段

只要某段时，先核对原片起止时间。以下示例截取 `00:40` 到 `01:25`，写到任务目录中的新文件。同名文件已经存在时，先另选文件名再运行。对纯音频，可用 `-vn -c:a pcm_s16le` 输出 WAV。

```bash
ffmpeg -nostdin -n -ss 40 -i "/path/to/video.mp4" -t 45 \
  -map '0:v:0?' -map 0:a:0 -c:v libx264 -c:a aac "/path/to/task/clip.mp4"
```

核对片段实际起止，记录原片文件名、SHA-256 和处理区间。后续命令将视频路径替换为 `clip.mp4`，预检和来源哈希均以该副本为准。成片外的字幕轨可回原片核对。片段内的时间戳从片段起点计，交付时说明口径，或换算回原片时间。

## 3. 预检媒体

```bash
python scripts/probe_media.py \
  "/path/to/video.mp4" \
  --output-dir "/path/to/output"
```

预检失败就先停，不继续宣称可以完整转写。

## 4. 双模型转写

```bash
python scripts/transcribe_local.py \
  "/path/to/video.mp4" \
  --output-dir "/path/to/output"
```

默认生成 `large-v3` 与 `medium` 两份原始结果。

## 5. 比较差异

```bash
python scripts/compare_transcripts.py \
  "/path/to/output/raw-large-v3.json" \
  "/path/to/output/raw-medium.json" \
  --output-dir "/path/to/output"
```

重点先看 `high` 风险检查点。

## 6. 有可见字幕时抽帧

```bash
python scripts/extract_review_frames.py \
  "/path/to/video.mp4" \
  "/path/to/output/review-points.json" \
  --output-dir "/path/to/output/review-frames"
```

默认最多处理 30 个高优先级检查点。全部处理：

```bash
--max-points 0
```

纯音频或没有成片字幕时跳过。

## 7. 生成约定稿件

按[输出格式](../references/output-format.md)选择模板。默认交付三份：

```text
逐字稿-校对版.md
文案-还原整理版.md
待确认疑点.md
```

其中“还原文案整理”只负责在不改变原意的前提下清理口头噪声和无意义重复，不等于创作性改写。

只要一种稿件时，按约定交付。未要求单独疑点清单时，把未确认项留在稿件或交付说明中。

## 8. 验收

```bash
python scripts/validate_outputs.py "/path/to/output"
```

脚本会校验不同模型、结果文件、来源哈希及差异文件结构。看到 `PASS｜完整交付有效` 后，还需确认人工校对完成、未确认项保留及完整性警告已说明，才能把任务称为完整完成。

只要逐字稿时使用 `--deliverables transcript`。`clean` 代表整理稿，`issues` 代表疑点清单，允许组合。指定稿件验收同样检查双模型、来源和需要复核的长空缺。

```bash
python scripts/validate_outputs.py "/path/to/output" --deliverables transcript
```

如果只是检查机器阶段：

```bash
python scripts/validate_outputs.py "/path/to/output" --machine-only
```
