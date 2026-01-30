# /**
#  * analysis.py
#  * 1局の解析
#  */

###########
### モジュール
###########
# 標準モジュール
import os
import sys
import datetime
# 自作モジュール
import calculate_summary_stats
from config import config
import katago_analyzer
import output
import sgf_utils

###########
### 1局の解析を行う関数
###########
def analyze_game(
        sgf_file_path,  
        csv_lock
    ):

    # 初期処理
    print(f"--- {os.path.basename(sgf_file_path)} の解析を開始 ---")
    proc = None
    start_time = datetime.datetime.now()
    
    try:
        # 準備とSGF情報の読み込み
        (game_tree, 
         board_size, 
         black_player, 
         white_player, 
         black_rank, 
         white_rank) = sgf_utils.load_sgf_and_get_game_info(sgf_file_path)

        moves = [] # これまでの手を記録 (KataGoへの入力用)
        all_move_data = [] # 出力用に1手ごとのデータを保持するリスト
        
        # 統計データ初期化
        stats = {
            'b': {'player_name': black_player, 'player_rank': black_rank, 'total_moves': 0, 
                  'same': 0, 'good': 0, 'bad': 0, 'good_sum': 0.0, 'bad_sum': 0.0},
            'w': {'player_name': white_player, 'player_rank': white_rank, 'total_moves': 0, 
                  'same': 0, 'good': 0, 'bad': 0, 'good_sum': 0.0, 'bad_sum': 0.0}
        }
        
        # KataGoプロセスを起動
        proc = katago_analyzer.start_katago_process()
        
        if (proc is not None):
            # 全着手の解析ループ (最大手数まで)
            for i, node in enumerate(game_tree.nodes):
                
                if (i == 0): continue # 最初のノードは情報ノードのためスキップ
                
                if (i > config.MAX_MOVE_TO_ANALYSIS): # 解析の最大手数に到達
                    break 

                # 着手情報の抽出
                if ('B' in node.properties):
                    color = 'b'
                    sgf_move = node.properties['B'][0]
                elif ('W' in node.properties):
                    color = 'w'
                    sgf_move = node.properties['W'][0]
                else:
                    continue

                # 着手の解析 (KataGoへの問い合わせ)
                (player_score, 
                 ai_best_score, 
                 score_diff, 
                 ai_best_move, 
                 gtp_move,
                ) = katago_analyzer.get_evaluation_and_scorediff(
                    proc, 
                    board_size, 
                    list(moves), 
                    sgf_move, 
                    color
                )
                
                moves.append([color, gtp_move])

                # 指標の計算と結果の格納
                if (player_score is not None):
                    current_stats = stats[color]
                    current_stats['total_moves'] += 1
                    category = ""
                    loss_value = 0.0
                    
                    # 好手・悪手・一致の判定
                    if (gtp_move == ai_best_move):
                        current_stats['same'] += 1
                        category = "一致"
                        loss_value = 0.0  # 一致手は損失なし
                    elif ((color == 'b' and score_diff >= 0.0) or (color == 'w' and score_diff <= 0.0)):
                        current_stats['good'] += 1
                        current_stats['good_sum'] += abs(score_diff)
                        category = "好手"
                        loss_value = -score_diff if color == 'b' else score_diff 
                    else:
                        current_stats['bad'] += 1
                        current_stats['bad_sum'] += abs(score_diff)
                        category = "悪手"
                        loss_value = abs(score_diff)

                    loss_value = round(abs(score_diff), 3) if (score_diff is not None) else 0.0
                    
                    # 1手ごとの解析結果をリストに格納
                    move_data = {
                        'player_color': color,          # プレイヤーの色(黒/白)
                        'move_number': len(moves),      # 手数
                        'gtp_move': gtp_move,           # プレイヤーの着手
                        'ai_best_move': ai_best_move,   # AIが考える最善手
                        'player_score': player_score,   # プレイヤーの評価値
                        'ai_best_score': ai_best_score, # AIの評価値
                        'score_diff': score_diff,       # 評価値の差(プレイヤーの手の評価値 - AIの評価値)
                        'category': category,           # 手の分類
                        'loss_value': loss_value,
                    }
                    all_move_data.append(move_data)
            
            # 統計結果の計算
            calculated_stats = calculate_summary_stats.calculate_summary_stats(stats)
            finish_time = datetime.datetime.now()

            try:
                # テキストファイルへログの書き出し
                output.write_log_to_text(
                    start_time,
                    finish_time,
                    sgf_file_path,
                    all_move_data, 
                    calculated_stats,
                )
                # CSVファイルへ統計情報の書き出し
                output.write_summary_to_csv(
                    calculated_stats, 
                    sgf_file_path, 
                    csv_lock
                )
                # CSVファイルへ詳細情報の書き出し
                output.write_detail_to_csv(
                    all_move_data, 
                    sgf_file_path, 
                    calculated_stats,
                    csv_lock
                )
            except Exception as e:
                print(f"エラー: {sgf_file_path}の書き出しに失敗 : {e}")
            
        else:
            raise Exception("エラー: KataGoプロセスを開始できません")

    except FileNotFoundError:
        print(f"エラー: SGFファイル '{sgf_file_path}' が見つかりません", file=sys.stderr)
    except Exception as e:
        print(f"解析中のエラー: {e}", file=sys.stderr)
        
    finally:
        if (proc):
            # プロセスを終了させる
            proc.terminate()
