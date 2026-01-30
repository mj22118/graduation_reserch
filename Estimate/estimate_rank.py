# /**
#  * estimate_rank
#  * ランク推定を行い誤差を計算する
# */

import pandas as pd
import numpy as np
import os
import sys
import unicodedata
import csv
from typing import Dict, Tuple
from scipy import stats
from remove_outliers import remove_outliers
from go_ranks import RANK_NAME_TO_INDEX, RANK_NAMES # type:ignore

###########
### 二乗和誤差を計算する関数
###########
def calculate_squared_error_sum(results):
    squared_error_sum = 0.0
    
    # 辞書からデータを取り出し、数値に変換
    for player, (actual_rank_str, _, predicted_rank_str) in results.items():
        # 実際のランクと推定ランクを数値にマッピング        
        try:
            actual_num = RANK_NAME_TO_INDEX.get(actual_rank_str, np.nan)
            predicted_num = RANK_NAME_TO_INDEX.get(predicted_rank_str, np.nan)
        except:
            actual_num = np.nan
            predicted_num = np.nan
            
        # データが有効な場合のみ計算
        if ((not np.isnan(actual_num)) and (not np.isnan(predicted_num))):
            error = actual_num - predicted_num
            squared_error_sum += error ** 2
            
    return float(squared_error_sum)

###########
### 表示のスペース数を取得する関数
###########
def get_display_width(text):
    width = 0
    for char in text:
        # unicodedata.east_asian_width で文字の幅を取得
        # 'F' (Fullwidth), 'W' (Wide) は 2 
        # 'H' (Halfwidth), 'Na' (Narrow), 'A' (Ambiguous) などは 1
        wc = unicodedata.east_asian_width(char)
        if wc in ('F', 'W'):
            width += 2
        else:
            width += 1
    return width


###########
### プレイヤーごとに推定結果を表示する関数
###########
def print_estimate_result(actual_rank, filtered_rates):
    NAME_COL_WIDTH = 25
    if (filtered_rates):
        print(" プレイヤー  | 平均損失 | 推定 | 誤差")
        print("-" * 40)
        for player, (_, rate, estimated_rank) in filtered_rates.items(): 
            current_width = get_display_width(player)
            padding_spaces = ' ' * (NAME_COL_WIDTH - current_width)
            if ((estimated_rank not in RANK_NAME_TO_INDEX) or (estimated_rank not in RANK_NAME_TO_INDEX)):
                rank_error = "N/A"
            else:
                R_actual = RANK_NAME_TO_INDEX[actual_rank]
                R_estimated = RANK_NAME_TO_INDEX[estimated_rank]
            rank_error =  R_estimated - R_actual

            print(f"{player}{padding_spaces} |    {rate:.3f} |  {estimated_rank:>3} | {rank_error:<+5}")
        print("-" * 40)
    else:
        print("フィルタリング条件を満たすプレイヤーが見つかりません。")

###########
### 推定の誤差を計算する関数
###########
def print_whole_rmse(
        NUM_TARGET_PLAYER,   # 棋譜数を満たすプレイヤー数 
        SHEET_NAMES,         # 推定対象の全ランク
        total_squared_error, # 二乗誤差の合計
    ):
    # 総合RMSEの計算と表示
    total_data_points = NUM_TARGET_PLAYER * len([s for s in SHEET_NAMES if s in RANK_NAME_TO_INDEX])
    
    print("=" * 40)
    print(f"総合評価結果 (全 {total_data_points} プレイヤー統合)")
    print("=" * 40)

    if (total_data_points > 0):
        mean_squared_error = total_squared_error / total_data_points
        final_rmse = round(np.sqrt(mean_squared_error), 3)
        print(f"総合ランク推定誤差 (RMSE): {final_rmse}")
    else:
        print("評価対象となる有効なデータ点がありません")

    return final_rmse

###########
### 推定結果をCSVに書き込む関数
###########
def write_rank_to_csv(
        RESULT_ESTIMATION_DIR,    # 保存先のディレクトリ
        evaluation_endpoint_move, # 評価終点手数 EEM
        threshold,                # 閾値 τ
        filtered_rates            # プレイヤーと推定ランクの辞書
    ):
    try:
        # 保存用フォルダがなければ作成
        if not os.path.exists(RESULT_ESTIMATION_DIR):
            os.makedirs(RESULT_ESTIMATION_DIR)

        # ファイル名を作成
        file_name = f"Result_EEM-{evaluation_endpoint_move:0>3}_TAU-{int(threshold*10)}.csv"
        file_path = os.path.join(RESULT_ESTIMATION_DIR, file_name)

        is_new_file = not os.path.exists(file_path)
        header = ["プレイヤー名", "実ランク", "推定ランク", "実ランク(int)", "推定ランク(int)"]
        
        # 書き込み
        with open(file_path, mode='a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)

            # ヘッダーを書く
            if (is_new_file):
                writer.writerow(header)
            
            # プレイヤーごとの結果をループで書き込み
            for player_id, result_tuple in filtered_rates.items():
                actual_rank_str = result_tuple[0]
                est_rank_str = result_tuple[2]
                
                data = [
                    player_id,
                    actual_rank_str,
                    est_rank_str,
                    RANK_NAME_TO_INDEX[actual_rank_str],
                    RANK_NAME_TO_INDEX[est_rank_str],
                ]
                writer.writerow(data)

    except Exception as e:
        print(f"エラー: CSVファイルへの詳細情報の書き込みに失敗 - {e}")

##########
### 平均損失からランク名を決定する関数
##########
def get_player_rank(average_mistake_rate, COEFF_A, COEFF_B):
    # 平均損失からインデックスを求める(実数値)
    estimated_index_float = (COEFF_A * average_mistake_rate) + COEFF_B
    
    # 推定インデックスを最も近い整数に丸める(インデックスの範囲を制限 (1 <= R <= 27))
    rounded_index = int(np.round(estimated_index_float))
    final_index = np.clip(rounded_index, 1, len(RANK_NAMES))
    
    # インデックスに対応するランク名を返す
    # インデックスは1から始まるため、リストのアクセスは [final_index - 1]
    return RANK_NAMES[final_index - 1]

##########
### 各プレイヤーのランクを推定する関数
##########
def analyze_player_rank_csv(
        DATA_ESTIMATION_DIR: str,      # データディレクトリ
        actual_rank: str,              # 実ランク（ファイル名の一部）
        evaluation_endpoint_move: int, # 評価終点手数
        threshold: float,              # τ
        NUM_GAMES_PER_PLAYER: int,     # 必要棋譜数
        NUM_TARGET_PLAYER: int,        # 必要プレイヤー数
        COEFF_A: float,                # 係数 A
        COEFF_B: float                 # 係数 B
    ):
    
    try:
        file_path = os.path.join(DATA_ESTIMATION_DIR, f"{actual_rank}.csv")
        df = pd.read_csv(file_path, header=None)
    except Exception as e:
        print(f"ファイル読み込みエラー ({actual_rank}): {e}")
        return {}

    # プレイヤー名列（1列目:黒, 2列目:白）
    black_players = df.iloc[:, 1].astype(str).str.strip()
    white_players = df.iloc[:, 2].astype(str).str.strip()
    
    # 損失データ（3列目〜指定手数分）
    # 列数制限: 3 + EEM まで
    loss_data = df.iloc[:, 3 : 3 + evaluation_endpoint_move]
    
    # プレイヤーごとの対局数をカウント
    all_players = pd.concat([black_players, white_players])
    player_counts = all_players.value_counts()
    
    # 条件を満たすプレイヤーを抽出
    target_players = player_counts[player_counts == NUM_GAMES_PER_PLAYER].index.tolist()
    
    if len(target_players) != NUM_TARGET_PLAYER:
        print(f"エラー: 人数の不一致 (ランク {actual_rank})")
        print(f"想定 {NUM_TARGET_PLAYER}人, 実際 {len(target_players)}人")
        sys.exit(1)

    results: Dict[str, Tuple[str, float, str]] = {}
    
    # 手番（列）ごとの黒白判定
    num_cols = loss_data.shape[1]
    col_indices = np.arange(num_cols)
    is_black_col = (col_indices % 2 == 0) # 0(1手目), 2(3手目)...
    is_white_col = (col_indices % 2 != 0) # 1(2手目), 3(4手目)...

    for player in target_players:
        # このプレイヤーが黒/白で参加している行(対局)を特定
        is_p_black = (black_players == player).values
        is_p_white = (white_players == player).values
        
        # 損失値をNumpy配列化
        p_loss_values = loss_data.apply(pd.to_numeric, errors='coerce').values
        
        # 抽出: (黒番の行 AND 黒番の列) OR (白番の行 AND 白番の列)
        # このプレイヤーが「黒」の対局における、「黒番（奇数手）」の損失
        losses_as_black = p_loss_values[is_p_black][:, is_black_col].flatten()
        
        # このプレイヤーが「白」の対局における、「白番（偶数手）」の損失
        losses_as_white = p_loss_values[is_p_white][:, is_white_col].flatten()
        
        # 結合してNaN除去
        all_losses = np.concatenate([losses_as_black, losses_as_white])
        all_losses = all_losses[~np.isnan(all_losses)]
        
        # 行ごとの平均を計算するロジック
        game_averages = []
        
        # 黒番として打った対局の平均
        if np.any(is_p_black):
            # その対局の黒番列だけの平均
            b_means = np.nanmean(p_loss_values[is_p_black][:, is_black_col], axis=1)
            game_averages.extend(b_means)
            
        # 白番として打った対局の平均
        if np.any(is_p_white):
            w_means = np.nanmean(p_loss_values[is_p_white][:, is_white_col], axis=1)
            game_averages.extend(w_means)
            
        # 局平均損失に対して外れ値を除去する
        processed_game_averages = remove_outliers(game_averages, threshold)
        player_average_loss = np.mean(processed_game_averages)
        
        # ランク推定
        est_rank = get_player_rank(player_average_loss, COEFF_A, COEFF_B)
        results[player] = (actual_rank, round(player_average_loss, 3), est_rank)
        
    return results

##########
### プレイヤーごとに平均損失を計算する関数(メインループ)
##########
def estimate_rank(
        DATA_ESTIMATION_DIR: str,      # CSVフォルダ
        RESULT_ESTIMATION_DIR: str,    # 結果出力フォルダ
        evaluation_endpoint_move: int, 
        threshold: float,
        NUM_GAMES_PER_PLAYER: int,
        NUM_TARGET_PLAYER: int,
        COEFF_A: float,
        COEFF_B: float
    ):
    
    total_squared_error = 0.0
    actual_rank_list = []
    estimated_rank_list = []
    
    # フォルダ内の有効なCSVファイルを取得
    try:
        all_files = os.listdir(DATA_ESTIMATION_DIR)
        TARGET_RANKS = [
            os.path.splitext(f)[0] for f in all_files 
            if f.endswith('.csv') and os.path.splitext(f)[0] in RANK_NAME_TO_INDEX
        ]
        # ランク順にソート
        TARGET_RANKS.sort(key=lambda x: RANK_NAME_TO_INDEX[x], reverse=True)
        
    except Exception as e:
        print(f"ディレクトリ読み込みエラー: {e}")
        return None, None, None

    for actual_rank in TARGET_RANKS:
        print("-" * 40)
        print(f"ランク {actual_rank} の解析結果")
        print("-" * 40)
        
        # 解析実行
        filtered_rates = analyze_player_rank_csv(
            DATA_ESTIMATION_DIR,
            actual_rank,
            evaluation_endpoint_move,
            threshold,
            NUM_GAMES_PER_PLAYER,
            NUM_TARGET_PLAYER,
            COEFF_A,
            COEFF_B
        )
        
        if not filtered_rates:
            continue

        # 結果表示
        print_estimate_result(actual_rank, filtered_rates)

        # データをリストに追加（相関係数用）
        for res in filtered_rates.values():
            actual_rank_list.append(RANK_NAME_TO_INDEX[res[0]])
            estimated_rank_list.append(RANK_NAME_TO_INDEX[res[2]])

        # CSV出力
        write_rank_to_csv(
            RESULT_ESTIMATION_DIR,
            evaluation_endpoint_move,
            threshold,
            filtered_rates
        )
        
        # RMSE計算
        sse = calculate_squared_error_sum(filtered_rates)
        total_squared_error += sse
        
        if NUM_TARGET_PLAYER > 0:
            rmse_sheet = np.sqrt(sse / NUM_TARGET_PLAYER)
            print(f"ランク推定誤差 (RMSE): {rmse_sheet:.3f} \n")

    # 全体のRMSEを計算
    total_players = NUM_TARGET_PLAYER * len(TARGET_RANKS)
    total_rmse = round(np.sqrt(total_squared_error / total_players), 3) if total_players > 0 else 0.0
    
    print(f"=== 総合結果 (全{total_players}プレイヤー)===")
    print(f"総合推定誤差 (RMSE): {total_rmse} ")

    # 相関係数とp値
    r, p = 0.0, 1.0
    if (len(actual_rank_list) > 1):
        r, p = stats.pearsonr(actual_rank_list, estimated_rank_list)
        print(f"相関係数 (r): {r:.3f}")
        print(f"p値 (p): {p:.4e}")

    return total_rmse