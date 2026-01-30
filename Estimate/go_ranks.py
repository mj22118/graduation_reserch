# /**
#  * rank_relation.py
#  * ランクにまつわる定数
# */

import numpy as np

# ランク名 (棋力上昇順に定義)
RANK_NAMES = np.array([
    "18k", "17k", "16k", "15k", "14k", 
    "13k", "12k", "11k", "10k", "9k", 
    "8k",  "7k",  "6k",  "5k",  "4k", 
    "3k",  "2k",  "1k",  "1d",  "2d", 
    "3d",  "4d",  "5d",  "6d",  "7d", 
    "8d",  "9d"
])

# ランクインデックス
RANK_INDICES = np.arange(0, len(RANK_NAMES))

# ランク名 -> インデックス (R) の辞書
RANK_NAME_TO_INDEX = {name: i for i, name in enumerate(RANK_NAMES)}
