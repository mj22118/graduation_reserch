# /**
#  * katago_analyzer.py
#  * KataGoのプロセス管理と解析ロジック
#  */

import subprocess
import json
import time
from config import config
import sgf_utils

###########
### KataGoのプロセスを起動する関数
###########
def start_katago_process():
    try:
        proc = subprocess.Popen(
            [config.KATAGO_PATH, "analysis", "-model", config.MODEL_FILE, "-config", config.CONFIG_FILE],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=config.SCRIPT_DIR
        )

        max_wait_time = 30 # タイムアウト時間：30秒
        start_time = time.time()

        while True:
            # タイムアウト
            if (time.time() - start_time > max_wait_time):
                print("エラー: KataGoの起動がタイムアウトしました。")
                proc.terminate()
                return None
            
            # 非ブロッキングでの読み取りを試みる
            line = proc.stderr.readline()
            
            if line:
                if (("Started, ready to begin handling requests") in line):
                    return proc
            
            # データがない場合は少し待つ
            time.sleep(0.5)

    except FileNotFoundError:
        print(f"エラー: KataGoの実行ファイルが見つかりません。パスを確認してください: {config.KATAGO_PATH}")
        return None
    except Exception as e:
        print(f"KataGoの起動中に予期せぬエラーが発生しました: {e}")
        return None

###########
### KataGoに解析を依頼し、評価値を取得する関数
###########
def get_evaluation_and_scorediff(katago_proc, board_size, moves_before_player_move, sgf_move, player_color):
    # 各リクエストにユニークなIDを割り当てる
    req_id_before = f"analysis_before_{time.time()}"
    req_id_after = f"analysis_after_{time.time()}"
    
    gtp_player_move = sgf_utils.sgf_to_gtp(sgf_move)

    # 1回目の解析リクエスト
    input_data_before = {
        "id": req_id_before,
        "moves": moves_before_player_move,               # これまでの着手
        "initialStones": [],                             # 盤上の初期配置
        "boardXSize": board_size,                        # 碁盤の横の大きさ
        "boardYSize": board_size,                        # 碁盤の縦の大きさ
        "komi": 6.5,                                     # コミ(目)
        "rules": "japanese",                             # ルールセット
        "analyzeTurns": [len(moves_before_player_move)], # 解析対象の手
    }

    try:
        katago_proc.stdin.write(json.dumps(input_data_before) + "\n")
        katago_proc.stdin.flush()
        
        # 1回目の応答が来るまで読み取りを繰り返す
        while True:
            line = katago_proc.stdout.readline()
            if (not line):
                raise IOError("KataGoプロセスが予期せず終了しました。")
            
            try:
                response = json.loads(line)
                # リクエストIDと応答のIDが一致するか確認
                if (response.get("id") == req_id_before):
                    # 応答に 'moveInfos' が存在するか確認
                    if ('moveInfos' in response):
                        ai_best_move = response['moveInfos'][0]['move']
                        ai_best_score = response['moveInfos'][0]['scoreLead']
                        break # 正しい応答を見つけたらループを抜ける
                    else:
                        print(f"警告: KataGoからの応答に 'moveInfos' が見つかりません。応答: {response}")
                        # 無関係な応答なので、次の行を読み取る
                        return None, None, None, None, None
            except json.JSONDecodeError as e:
                # JSON形式でないログ行は無視して次の行へ
                print(f"警告: JSON形式でない行を無視します。行: {line.strip()}")
                return None, None, None, None, None
    except Exception as e:
        print(f"KataGo応答解析中にエラーが発生しました (1回目): {e}")
        return None, None, None, None, None

    # プレイヤーの着手とAIが考える最善手が同じ場合
    if (gtp_player_move == ai_best_move):
        # 着手の評価値(=最善手の評価値)、悪手度(=0.000)、AIの最善手を返す
        return ai_best_score, ai_best_score, 0.000, ai_best_move, gtp_player_move

    # 2回目の解析リクエスト
    moves_after_player_move = moves_before_player_move + [[('b' if len(moves_before_player_move) % 2 == 0 else 'w'), gtp_player_move]]
    input_data_after = { # 項目は1回目と同じ
        "id": req_id_after,
        "moves": moves_after_player_move,
        "initialStones": [],
        "boardXSize": board_size,
        "boardYSize": board_size,
        "komi": 6.5,
        "rules": "japanese",
        "analyzeTurns": [len(moves_after_player_move)],
    }
    
    try:
        katago_proc.stdin.write(json.dumps(input_data_after) + "\n")
        katago_proc.stdin.flush()
        
        # 2回目の応答が来るまで読み取りを繰り返す
        while True:
            line = katago_proc.stdout.readline()
            if (not line):
                raise IOError("KataGoプロセスが予期せず終了しました。")
            
            try:
                response = json.loads(line)
                if response.get("id") == req_id_after:
                    if ('moveInfos' in response):
                        player_score = response['moveInfos'][0]['scoreLead']
                        break
                    else:
                        print(f"警告: KataGoからの応答に 'moveInfos' が見つかりません。応答: {response}")
                        return None, None, None, None, None
            except json.JSONDecodeError as e:
                print(f"警告: JSON形式でない行を無視します。行: {line.strip()}")
                return None, None, None, None, None

    except Exception as e:
        print(f"KataGo応答解析中にエラーが発生しました (2回目): {e}")
        return None, None, None, None, gtp_player_move
    
    # 評価値の差を計算 (プレイヤーの手の評価値 - AIの評価値)
    score_diff = player_score - ai_best_score

    # 着手の評価値、最善手の評価値、評価値の差、AIの最善手を返す
    return player_score, ai_best_score, score_diff, ai_best_move, gtp_player_move