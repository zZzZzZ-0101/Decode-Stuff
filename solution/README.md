# solution/ — 独立求解程序

| 文件 | 内容 |
|---|---|
| `solve.py` | 从卷面到明文的完整求解，约 200 行，只读 `../challenge/challenge.txt`，不依赖 `research/` |
| `expected_output.txt` | `python3 solution/solve.py` 的完整输出，用于比对 |

## 运行

```bash
pip install -r requirements.txt      # pypinyin
python3 solution/solve.py            # 打印各步自检与明文
python3 solution/solve.py --quiet    # 只打印明文
```

可以在任意工作目录下运行。已在 Python 3.13 + pypinyin 0.55 上测试。pypinyin 0.47–0.55 之间各版本的音节表结果一致。

## 程序结构

| 函数 | 对应步骤 | 说明 |
|---|---|---|
| `read_challenge` | 卷面解析 | 取出题引 8 句与 230 个实字 |
| `syllable_table` | 音节表 | GB2312 6763 字的默认读音，去掉空韵母与轻声，共 1194 个带调音节 |
| `Rings.ring` | 语境子环 | 固定另两维，只在能相拼的子集上成环 |
| `round_keys` | 数 + 展卷 | 由种子生成 sbox，56 长状态经 115 转得出轮钥 |
| `run_chain` | 归 | 三相移位与前位回声；`sign=-1` 解密，`+1` 加密 |
| `spiral_order` | 织位 | 23×5 网格的回字形逆时针螺旋 |
| `solve` | 主流程 | 依次执行各步并断言自检 |

## 自检

程序在运行中做以下断言，任一失败即中止：

1. 卷面解析得到题引 8 句、正文 23 行、230 个实字。
2. 115 个密文音节全部合法；只有一个方向能拼出合法音节的 34 对，其方向与轮钥奇偶全部吻合。
3. 把解出的音节重新加密，逐位复现 115 个密文音节。

最后把明文的汉字读法逐字取默认读音，与解出的音节对照，并打印结果：112/115 一致。不一致的 3 处都是轻声字（"们"和两处"的"），命题方编码时记为第二声。

算法的完整说明与手算实例见 [`../writeup/WRITEUP.md`](../writeup/WRITEUP.md)。
