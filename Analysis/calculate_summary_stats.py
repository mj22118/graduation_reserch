# /**
#  * calculate_summary_stats
#  * 解析結果から統計情報の計算
#  */

def calculate_summary_stats(stats):
    summary_data = {}
    for color, player_stats in stats.items():
        # 解析結果の取得
        total_moves = player_stats['total_moves'] # 手数
        same = player_stats['same']               # 一致数 
        good = player_stats['good']               # 好手数
        bad = player_stats['bad']                 # 悪手数
        good_sum = player_stats['good_sum']       # 好手の総評価
        bad_sum = player_stats['bad_sum']         # 悪手の総評価
        
        # 統計情報を計算して辞書にまとめる
        summary_data[color] = {
            'player_name': player_stats['player_name'],
            'player_rank': player_stats['player_rank'],
            'total_moves': total_moves,
            'same_rate': (same / total_moves) if (total_moves > 0) else 0,                   # 一致率
            'good_rate': (good / (good + bad)) if ((good + bad)) > 0 else 0,                 # 好手率
            'bad_rate': (bad / (good + bad)) if ((good + bad) > 0) else 0,                   # 悪手率
            'avg_good_loss': (good_sum / total_moves) if (total_moves > 0) else 0,           # 平均好手
            'avg_bad_loss': (bad_sum / total_moves) if (total_moves > 0) else 0,             # 平均悪手
            'avg_total_loss': (bad_sum - good_sum) / total_moves if (total_moves > 0) else 0 # 平均損失
        }
    return summary_data