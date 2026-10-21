# research/ — 实验脚本

本目录是破译过程中的全部探索性脚本，按假设族分目录。最终解法不依赖这里的代码，见 [`../solution/solve.py`](../solution/solve.py)。各脚本的结论汇总在 [`../writeup/REPORT.md`](../writeup/REPORT.md) 第 6–8 节与第 14–15 节，逐轮记录见 [`../notes/failed_attempts.md`](../notes/failed_attempts.md)。

所有脚本都可在任意工作目录下运行，例如 `python3 research/h03_fanqie_pairs/line_pairs.py`。

## 共享模块

| 文件 | 内容 |
|---|---|
| `data.py` | 题引、正文、分句与逐字拼音拆分（S21 / S23 两种口径） |
| `legal.py` | 合法音节表：GB2312 6763 字的全部读音，两种声韵切分口径 |
| `strokes.py` | 题引与正文全部用字的规范笔画 |

## 阶段一：卷面盲测（补遗之前）

判据取命题方自己的陈述：正确解密后每个位置都是合法音节，错误密钥则必然出现非法音节。

| 目录 | 假设 | 结论 |
|---|---|---|
| `h01_stream_shift/` | 声母流与韵母流错位、仿射重排（6 种阅读顺序 × 2 种口径）；`results.txt` 为输出 | 否定：最高 81.3%，随机最大 74–76% |
| `h03_fanqie_pairs/` | 严格反切配对：相邻、隔 115、镜像、左右句同槽、列配对等 | 多数否定；**`line_pairs.py`：行内相邻反切对 105/115，z ≈ 6.1**，即后来确认的"切"层 |
| `h05_periodic_key/` | 周期密钥（维吉尼亚，周期 1–60）与一阶链式差分；题引笔画作密钥 | 否定：与对照组无差别 |
| `h07_stroke_keys/` | 笔画密钥：八机关字、56 字滚动、各句笔画和、自密钥，共 1248 组配置 | 否定：100% 合法的为 0 组 |
| `h17_statistics/` | 正文是否为密码装置的直接输出：字频、重复、分层、与笔画的相关 | 正文用字是按诗意挑选的，不是装置的直接输出 |
| `h18_single_letter/` | 每字只携带一个"字母"（声 / 韵 / 调轮取、槽位指派、变长切分） | 否定：未达全部合法 |
| `h20_fanqie_stream/` | 在 115 个反切音节上检验周期笔画密钥与链式差分 | 否定（后来知道密钥来自 56 长状态展卷，非周期） |

## 阶段二：按《四处补遗》解密

| 文件 | 内容 |
|---|---|
| `h30_decrypt/spec.py` | 补遗的实现：sbox 四种约定、展卷、正倒、语境子环、三相环序、回声，加密与解密 |
| `decode.py` | 另一份独立实现（由 Gemini 编写），与 `spec.py` 逐位一致，作交叉验证 |
| `h30_decrypt/run_version.py` | 在当前 pypinyin 版本下跑完整解密并打分，用于对比不同版本的音节表 |

## 阶段三：织位搜索

| 文件 | 内容 | 结论 |
|---|---|---|
| `h30_decrypt/weave.py` | 固定织位族：倒序、交错、对折、栅栏、各宽度网格的行 / 列 / 蛇形 / 螺旋 / 斜扫 | 无信号 |
| `h30_decrypt/columnar.py` | 带密钥列序的列移位（5 列穷举，23 列集束搜索） | 无信号 |
| `h30_decrypt/keyweave.py` | 密钥驱动织位：约瑟夫环、按轮钥排序、步进回填（286 种） | 无信号 |
| `h30_decrypt/anagram.py` | 诊断：不受约束的重排（模拟退火）能达到的连读覆盖 | 覆盖 99，支持"音节正确、问题在顺序" |
| `h30_decrypt/gridpath.py` | **通用网格织位**：所有 115–130 格网格上"写入路径 × 读出路径"的组合（3875 种） | **命中："23×5 按行写入、回字形螺旋读出"，覆盖 77，随机 2000 次最高 62** |
| `h30_decrypt/lm.py` | 可读性打分：带调拼音词库（词组读音 + 逐字默认读音）上的连读覆盖 | 打分工具 |

## jieba 词频表

`h30_decrypt/lm.py`（以及调用它的 `run_version.py`）需要 jieba 的词频表 `dict.txt`。本仓库不收录该文件，可按下面的方式获取：

```bash
pip download jieba==0.42.1 --no-deps --no-binary :all: -d /tmp/jieba
tar -xzf /tmp/jieba/jieba-0.42.1.tar.gz -C /tmp/jieba
export JIEBA_DICT=/tmp/jieba/jieba-0.42.1/jieba/dict.txt
```

首次运行时会在 `h30_decrypt/` 下生成缓存 `lex.pkl`，该文件已列入 `.gitignore`。

## 依赖

Python 3，`pypinyin`、`numpy`，见根目录 `requirements.txt`。
