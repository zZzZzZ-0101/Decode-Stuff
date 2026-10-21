# notes/ — 分轮工作日志

本目录是破译过程中逐轮维护的工作文档，Run 1–9 的推导、证伪和变更都记在这里。格式沿用 Gemini（AI Studio）建立的结构，每次变动都登记在 `notes.md` 第 5 节。

| 文件 | 内容 |
|---|---|
| `problem.md` | 题目：卷面、指令、材料清单 |
| `observations.md` | 观测：笔画表、正倒计数、首位回声、解密音节的统计特征、明文 |
| `failed_attempts.md` | 证伪记录：卷面盲测、补遗实现、织位搜索各阶段的全部失败尝试与数据 |
| `possible_patterns.md` | 规律：已确认的各层规则（种子、sbox、展卷、切、归、音节表、织位） |
| `notes.md` | 推导日志、交接建议、历次运行耗时与用量、变更记录 |
| `verification/verify_56state_pdf.py` | 验证：sbox 四种约定的消融，115 对反切与子环解密 |
| `verification/verify_plaintext_16.py` | 验证：回声链自同步，115 音节完整对照 |

## 轮次

| 轮次 | 执行方 | 内容 |
|---|---|---|
| Run 1–5 | Gemini（AI Studio） | 补遗装置复现、sbox 约定、自同步验证，建立本目录 |
| Run 6 | Claude Code | 合入 Run 1–5 成果，与 `research/h30_decrypt/` 交叉核对，更正文档中与卷面或计算不符之处 |
| Run 7 | Claude Code | 密钥驱动织位、回声方向检验、重排诊断 |
| Run 8 | Claude Code | 网格"写入 × 读出路径"通用枚举，**解出织位，读出明文** |
| Run 9 | Claude Code | 仓库发布整理 |

## 关于更正记录

Run 1–5 的笔记中有若干内容与卷面或计算结果不符：题引、sbox、正倒计数、首位回声，以及一段没有计算依据的"明文"。这些内容已在 Run 6 更正，原处保留"更正记录"注明改了什么、为什么改。

验证脚本从 `research/` 导入共享模块，运行方式：`python3 notes/verification/verify_56state_pdf.py`。
