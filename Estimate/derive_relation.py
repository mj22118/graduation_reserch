# /**
#  * derive_relation.py
#  * 最小二乗法によりランク推定の係数 a, b を導出し出力する。
# */

import numpy as np
import os
import csv
import pandas as pd
from remove_outliers import remove_outliers
from go_ranks import RANK_NAME_TO_INDEX # type:ignore

###########
### ランクごとに平均損失を計算する関数
###########
def analyze_turn_loss(
        DATA_RELATION_DIR,        
        actual_rank,             
        evaluation_endpoint_move,
        threshold,  
    ):
    try:
        # CSV読み込み
        file_path = os.path.join(DATA_RELATION_DIR, f"{actual_rank}.csv")
        df = pd.read_csv(file_path, header=None)
        df = df.iloc[1:] # ヘッダ行をカット
        df = df.dropna(subset=[0]) # 1列目が空の行をカット

    except Exception as e:
        print(f"ファイル読み込みエラー: {e}")
        return []

    # 着手を取得
    mistake_rates_df = df.iloc[:, 3 : 3 + evaluation_endpoint_move]
    all_moves = pd.to_numeric(mistake_rates_df.values.flatten(), errors='coerce')
    valid_moves = all_moves[~np.isnan(all_moves)] # 有効な数値だけを抽出
    
    if (len(valid_moves) == 0):
        return None, None

    # ランクにおける平均損失とその標準偏差を計算
    rank_loss_avg = round(np.mean(valid_moves), 3)
    rank_loss_std = round(np.std(valid_moves), 3)
    
    # 平均と標準偏差をタプルで返す
    return rank_loss_avg, rank_loss_std

###########
### ランクと平均損失の関係をCSVに書きこむ関数
###########
def write_relation_to_csv(
        RESULT_RELATION_DIR,      # CSVを保存するディレクトリ（フォルダ）
        evaluation_endpoint_move, # 評価終点手数（ファイル名の一部にする）
        threshold,                # 閾値 τ
        actual_rank,              # 実ランク
        avg,                      # ランクの平均損失
        std                       # その標準偏差
    ):
    try:
        # ディレクトリがない場合は作成
        if (not os.path.exists(RESULT_RELATION_DIR)):
            os.makedirs(RESULT_RELATION_DIR)

        # ファイル名を作成
        file_name = f"Relation_EEM-{evaluation_endpoint_move:0>3}_TAU-{int(threshold*10)}.csv"
        file_path = os.path.join(RESULT_RELATION_DIR, file_name)
        
        is_new_file = not os.path.exists(file_path)
        header = ["ランク", "ランク(int)", "平均損失", "標準偏差"]

        # データの書き込み
        with open(file_path, mode='a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            if is_new_file:
                writer.writerow(header)
            
            data = [
                actual_rank,
                RANK_NAME_TO_INDEX[actual_rank],
                round(avg, 3),
                round(std, 3)
            ]
            writer.writerow(data)

    except Exception as e:
        print(f"CSV書き出しエラー: {e}")

###########
### 係数 a, b を決定する関数
###########
def decide_coefficient(X_loss, Y_rank):
    print("\n=== 集計結果 ===")
    # NumPy配列に変換
    X = np.array(X_loss)
    Y = np.array(Y_rank)

    # 最小二乗法（1次関数、線形回帰）を実行
    a, b = np.polyfit(X, Y, 1)
    print(f"推定関係式   : y = {a:.3f} * x + {b:.3f}")

    # 相関係数 r と 決定係数 R^2 の計算
    correlation_matrix = np.corrcoef(X_loss, Y_rank)
    r = correlation_matrix[0, 1]
    R_squared = r**2
    print(f"相関係数(r)  : {r:.3f}")
    print(f"決定係数(R^2): {R_squared:.3f}" + '\n')

    return a, b

###########
### ランクと平均損失の関係を導く関数（CSVディレクトリ対応版）
###########
def derive_relation(
        DATA_RELATION_DIR,        # CSVファイルが格納されているフォルダ
        RESULT_RELATION_DIR,      # 結果（CSV）を記録するフォルダ
        evaluation_endpoint_move, # 評価終点手数
        threshold,                # 閾値 τ
    ):
    # 指定されたディレクトリ内のCSVファイルからランク名を取得
    try:
        # フォルダ内のファイル名を取得し、".csv" で終わるもの
        # かつ、拡張子を除いた名前が RANK_NAME_TO_INDEX に定義されているものに限定
        all_files = os.listdir(DATA_RELATION_DIR)
        RANK_NAMES = [
            os.path.splitext(f)[0] for f in all_files 
            if f.endswith('.csv') and os.path.splitext(f)[0] in RANK_NAME_TO_INDEX
        ]
        
        # ランク順に並び替える
        RANK_NAMES.sort(key=lambda x: RANK_NAME_TO_INDEX[x], reverse=True)
        
        if (not RANK_NAMES):
            print(f"警告: {DATA_RELATION_DIR} 内に有効なCSVファイルが見つかりません。")
            return None, None

    except Exception as e:
        print(f"エラー: {DATA_RELATION_DIR} の読み込み中にエラー: {e}")
        return None, None

    X_loss = [] # 平均損失
    Y_rank = [] # ランクインデックス

    # 各ランクのCSVファイルを順次処理
    for actual_rank in RANK_NAMES:
        # ランクごとに平均損失とその標準偏差を求める
        rank_loss_avg, rank_loss_std = analyze_turn_loss(
                DATA_RELATION_DIR,        # データフォルダ
                actual_rank,              # 実ランク名
                evaluation_endpoint_move, # 評価終点手数
                threshold,                # 閾値 τ
            )
        
        if (rank_loss_avg):
            X_loss.append(rank_loss_avg)
            Y_rank.append(RANK_NAME_TO_INDEX[actual_rank])

            print(f"--- {actual_rank} ランクの統計 ---")
            print(f"Avg.: {rank_loss_avg:.3f} 目")
            print(f"SD  : {rank_loss_std:.3f} 目")

            # 結果をCSVに出力
            write_relation_to_csv(
                RESULT_RELATION_DIR,      # 保存先フォルダ
                evaluation_endpoint_move, # 評価終点手数
                threshold,                # 閾値 τ
                actual_rank,              # 実ランク名
                rank_loss_avg,            # 平均
                rank_loss_std             # 標準偏差
            )
    
    # 係数 a, b を決定する（回帰分析）
    a, b = decide_coefficient(X_loss, Y_rank)

    return a, b