# /**
#  * remove_outliers
#  * リストから外れ値を除去する
# */

import numpy as np

### 処理前リスト： original_list
### 処理後リスト： processed_list
def remove_outliers(original_list, threshold):
    x = np.array(original_list)
    # 指標の計算
    median_x = np.median(x) # 中央値 (Median)
    abs_dev = np.abs(x - median_x) 
    mad = np.median(abs_dev) # 中央絶対偏差 (MAD)
    if (mad == 0): # データが全て同じ場合、外れ値を除去しない
        return original_list

    # 修正Zスコア (Modified Z-Score) の計算
    scaling_constant = 0.6745 # スケーリング定数
    modified_z_scores = scaling_constant * np.abs(x - median_x) / mad

    # 外れ値の特定と除去
    is_not_outlier = np.abs(modified_z_scores) < threshold
    processed_list = x[is_not_outlier].tolist()

    return processed_list
