# 共享数据：题引 / 正文 / 拼音拆分
from pypinyin import pinyin, Style
from collections import Counter

TIYIN = ["万山霜叶下秋烟","千回锦字未成篇","灯深帘底藏雁足","谁家玉笛切霜天",
         "静数冰弦骨亦清","一寸回文织未眠","凭君验取灯前字","字归其位月归川"]

ZHENGWEN_LINES = """红蕊垂兮染江，涌晓霞兮浪声。
苍醉菊兮柳春，芳阶蝶兮云朵。
茶烟青兮波明，照在芦兮天高。
染梅桨兮星波，露荷阁兮问雁。
汀野翠兮闻箫，云舞开兮约江。
舞蝶川兮亭台，濯暖柳兮清池。
竹乖莺兮黄菊，静水岸兮染碧。
柳酒岸兮春兰，爱晨满兮山长。
秋箫碧兮灯厦，飘香约兮望洲。
清曲起兮暖浦，闲云鱼兮舞天。
归路松兮春山，瓦芦湖兮溪笛。
梅来采兮归晓，月玉帘兮蝶骋。
萤问桂兮染朵，露山梅兮阳雁。
晨池菊兮浅开，春昼翠兮年长。
野烟雨兮柳秀，溪鹤风兮山展。
芦潮汐兮曲柔，蕙守兰兮暖朗。
阶菊兰兮近妙，露檐鸟兮开航。
舒萍轻兮觉径，雨飘萍兮凭飞。
唤深林兮飞翠，松窗兰兮舟涛。
荷华曲兮雁阵，梅满引兮歌孔。
露野秋兮约碧，湖塔明兮唤水。
雪韵茶兮蝶莺，月黄花兮看塔。
帘带碧兮默立，文鱼亮兮闻花。""".split("\n")

# 46 分句，每句 5 字（去掉兮）
CLAUSES = []
for ln in ZHENGWEN_LINES:
    ln = ln.strip("。")
    for half in ln.split("，"):
        CLAUSES.append(half.replace("兮", ""))
assert len(CLAUSES) == 46 and all(len(c) == 5 for c in CLAUSES)
TEXT = "".join(CLAUSES)          # 230 字，逐分句顺序
FREQ = Counter(TEXT)

INITIALS = ['b','p','m','f','d','t','n','l','g','k','h','j','q','x','zh','ch','sh','r','z','c','s','y','w']

def split_py(ch, heteronym=False):
    """返回 (声母, 韵母, 声调) 列表；声母按 23 声母表(含 y w)切分"""
    res = []
    for p in pinyin(ch, style=Style.TONE3, heteronym=heteronym, neutral_tone_with_five=True)[0]:
        tone = int(p[-1]) if p[-1].isdigit() else 5
        s = p.rstrip("012345")
        ini = ''
        for i in sorted(INITIALS, key=len, reverse=True):
            if s.startswith(i):
                ini = i; break
        res.append((ini, s[len(ini):], tone, s))
    return res

PY = {c: split_py(c)[0] for c in set(TEXT) | set("".join(TIYIN))}

# 用户仓库 Claude.md 中给出的笔画表（已核对过的简体笔画）
from strokes import STROKES
