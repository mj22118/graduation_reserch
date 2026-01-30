# /**
#  * text_writer
#  * 解析結果のテキストファイル出力
#  */

import os
import sys
from config import config

###########
### テキストファイルのヘッダを生み出す関数
###########
def generate_analysis_header(
        sgf_file_path, 
        max_move_to_analysis, 
        black_player, 
        white_player
    ):
    # 文字化けしたプレイヤー名を強制的に戻す
    encoded_black_player = (black_player.encode('cp1252', errors='ignore')).decode('utf-8', errors='ignore')
    encoded_white_player = (white_player.encode('cp1252', errors='ignore')).decode('utf-8', errors='ignore')
    # 解析結果のヘッダ行をリストとして生成する
    log_lines = []
    log_lines.append(f"SGFファイル: {sgf_file_path}")
    log_lines.append(f"解析の上限手数: {max_move_to_analysis}")
    log_lines.append(f"黒番プレイヤー: {black_player} ({encoded_black_player})")
    log_lines.append(f"白番プレイヤー: {white_player} ({encoded_white_player})")
    log_lines.append("-"*70)
    log_lines.append("手番 | 着手 | AI最善手 | 評価値     | AI最善差   | 評価値の差 | 分類")
    log_lines.append("="*70)
    return log_lines

###########
### テキストファイルの着手情報を生み出す関数
###########
def generate_analysis_moves(all_move_data):
    log_lines = []
    for data in all_move_data:
        score_change = data['score_diff'] if (data['player_color'] == 'b') else ((-1) * data['score_diff'])
        # 文字列として生成
        log_line = f"{data['move_number']:>4} | {data['gtp_move']:<4} | {data['ai_best_move']:<8} | {data['player_score']:>10.3f} | {data['ai_best_score']:>10.3f} | {score_change:>+10.3f} | {data['category']:<8}"
        log_lines.append(log_line)
    return log_lines

###########
### テキストファイルの統計情報を生み出す関数
###########
def generate_analysis_stats(calculated_stats):
    log_lines = []
    log_lines.append("="*70)
    log_lines.append("\n<棋譜全体の統計情報>")
    
    for color, player_data in calculated_stats.items():
        player_name = player_data['player_name']
        
        log_lines.append(f"--- {player_name} ({'黒番' if color == 'b' else '白番'}) ---")
        if (player_data['total_moves'] > 0):
            log_lines.append(f"総手数: {player_data['total_moves']}")
            log_lines.append(f"一致率: {player_data['same_rate'] * 100:.2f}%")
            
            if (player_data['good_rate'] + player_data['bad_rate']) > 0:
                log_lines.append(f"好手率: {player_data['good_rate'] * 100:.2f}%")
                log_lines.append(f"悪手率: {player_data['bad_rate'] * 100:.2f}%")
                log_lines.append(f"平均好手: {player_data['avg_good_loss']:.3f}")
                log_lines.append(f"平均悪手: {player_data['avg_bad_loss']:.3f}")
                log_lines.append(f"平均損失: {player_data['avg_total_loss']:.3f}")
            else:
                log_lines.append("好手および悪手のデータがありません。")
        else:
            log_lines.append("分析対象の手がありませんでした。")
    
    log_lines.append("\n" + "="*70) # ログの末尾に区切り線を追加
    return log_lines

###########
### テキストに書きだす関数
###########
def write_log_to_text(
        start_time, 
        finish_time, 
        sgf_file_path, 
        all_move_data, 
        calculated_stats
    ):

    # 定数の読み込み
    output_dir = config.OUTPUT_DIR
    max_moves_to_analyze = config.MAX_MOVE_TO_ANALYSIS
        
    # ログファイル名の決定
    sgf_filename = os.path.splitext(os.path.basename(sgf_file_path))[0]
    dt_filename_format = start_time.strftime("%Y%m%d_%H%M%S")
    log_file_name = f"Result_{dt_filename_format}_{sgf_filename}.txt"
    log_file_path = os.path.join(output_dir, log_file_name)
    
    dt_log_format = "%Y年%m月%d日 %H時%M分%S秒"
    
    start_time_str = start_time.strftime(dt_log_format)
    finish_time_str = finish_time.strftime(dt_log_format)

    black_player = calculated_stats['b']['player_name']
    white_player = calculated_stats['w']['player_name']

    # ファイルに書き込む内容を生成
    analysis_header_content = generate_analysis_header(
        sgf_file_path, 
        max_moves_to_analyze, 
        black_player, 
        white_player
    )
    analysis_moves_content = generate_analysis_moves(all_move_data)
    analysis_stats_content = generate_analysis_stats(calculated_stats)
    content = ([f"[開始] {start_time_str}\n"] 
               + analysis_header_content 
               + analysis_moves_content
               + analysis_stats_content
               + [f"\n[終了] {finish_time_str}\n"])
    
    try:
        # ファイルの生成、書き出し、クローズを一括実行
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(content))
        
    except Exception as e:
        sys.stdout = sys.__stdout__
        print(f"エラー: {sgf_file_path}のテキストファイルの生成に失敗 - {e}")