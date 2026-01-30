# /**
#  * csv_writer.py
#  * 解析結果のエクセル出力
#  */

import csv
import os
from config import config # configオブジェクトからパスを取得するため
import multiprocessing as mp # Lockオブジェクトの型ヒント用

###########
### CSVへ統計情報を書きだす関数
###########
def write_summary_to_csv(
        calculated_stats, 
        sgf_file_path, 
        csv_lock
    ):

    # ロックを取得し、排他的なアクセスを開始
    csv_lock.acquire()
    
    try:
        csv_file = config.SUMMARY_CSV_PATH 
        is_new_file = not os.path.exists(csv_file)
        
        # ヘッダー定義
        header = [
            "ファイル名", "プレイヤー名", "ランク", "手数", "一致率", "好手率", 
            "悪手率", "平均好手", "平均悪手", "平均損失"
        ]
        
        with open(csv_file, mode='a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            # 新規ファイルならヘッダーを書き込む
            if (is_new_file):
                writer.writerow(header)
            
            # 統計情報を書きこむ
            for color, player_data in calculated_stats.items():
                data = [
                    os.path.basename(sgf_file_path),
                    player_data['player_name'],
                    player_data['player_rank'],
                    int(player_data['total_moves']),
                    round(player_data['same_rate'], 3),
                    round(player_data['good_rate'], 3),
                    round(player_data['bad_rate'], 3),
                    round(player_data['avg_good_loss'], 3),
                    round(player_data['avg_bad_loss'], 3),
                    round(player_data['avg_total_loss'], 3)
                ]
                writer.writerow(data)

    except Exception as e:
        print(f"エラー: CSVファイルへの統計情報の書き込みに失敗 - {e}")

    finally:
        csv_lock.release()

###########
### CSVへ1手ごとの詳細情報を書きだす関数
###########
def write_detail_to_csv(
        move_datas, 
        sgf_file_path, 
        calculated_stats,
        csv_lock, 
    ):
    
    csv_lock.acquire()
    
    try:
        csv_detail_file = config.DETAIL_CSV_PATH
        is_new_file = not os.path.exists(csv_detail_file)

        # プレイヤー情報を取得
        black_rank = calculated_stats['b'].get('player_rank', 'Other')
        black_player = calculated_stats['b'].get('player_name', '-')
        white_player = calculated_stats['w'].get('player_name', '-')
        
        # ヘッダー作成 (ファイル名, 黒, 白, 1手目, 2手目, ...)
        header = ["ファイル名", "ランク(黒)", "プレイヤー(黒)", "プレイヤー(白)"]
        for i in range(1, config.MAX_MOVE_TO_ANALYSIS + 1):
            header.append(f"{i}")

        with open(csv_detail_file, mode='a', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            if (is_new_file):
                writer.writerow(header)

            # 1行分のデータを作成
            # 最初の4列：基本情報
            row_data = [
                os.path.basename(sgf_file_path),
                black_rank,
                black_player,
                white_player
            ]
            
            # 5列目以降：各手の損失値
            for i in range(config.MAX_MOVE_TO_ANALYSIS):
                if (i < len(move_datas)):
                    row_data.append(move_datas[i]['loss_value'])
                else:
                    row_data.append(None) # 対局が短い場合は空欄
            
            writer.writerow(row_data)

    except Exception as e:
        print(f"エラー: CSVファイルへの詳細情報の書き込みに失敗 - {e}")

    finally:
        csv_lock.release()