# /**
#  * main.py
#  * 悪手度からランクを推定するプログラム
#  *
#  * Author : 成田知史
#  * Number : 221205118
# */

import configparser
import os
import sys
from derive_relation import derive_relation
from estimate_rank import estimate_rank
from export_rmse import export_rmse 

# 定数の設定ファイル
CONFIG_FILE = 'estimate_config.ini'

###########
### 設定を読み込む関数
###########
def load_config(file_path: str = CONFIG_FILE):
    config = configparser.ConfigParser()
    settings = {}
    
    # ファイルが見つからない場合はエラーを発生させる
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"設定ファイル '{file_path}' が見つかりません。")

    # ファイルを読み込む
    config.read(file_path, encoding='utf-8')
    
    # 読み込んだ値を適切な型に変換して辞書に格納
    try:
        # [PATHS]
        settings['DATA_RELATION_DIR'] = config.get('PATHS', 'DATA_RELATION_DIR')
        settings['DATA_ESTIMATION_DIR'] = config.get('PATHS', 'DATA_ESTIMATION_DIR')
        settings['RESULT_RELATION_DIR'] = config.get('PATHS', 'RESULT_RELATION_DIR')
        settings['RESULT_ESTIMATION_DIR'] = config.get('PATHS', 'RESULT_ESTIMATION_DIR')
        settings['DETAILS_DIR'] = config.get('PATHS', 'DETAILS_DIR')
        settings['RESULT_RMSE_CSV'] = config.get('PATHS', 'RESULT_RMSE_CSV')
        settings['RESULT_RMSE_TEXT'] = config.get('PATHS', 'RESULT_RMSE_TEXT')
        
        # [RANGES]
        # 評価終点手数 (EEM) のリスト化
        eem_str = config.get('RANGES', 'EEM_LIST')
        settings['EEM_LIST'] = [int(x.strip()) for x in eem_str.split(',') if x.strip()]
        # 閾値 (Threshold) のリスト化
        th_str = config.get('RANGES', 'THRESHOLD_LIST')
        settings['THRESHOLD_LIST'] = [float(x.strip()) for x in th_str.split(',') if x.strip]

        # [ANALYSIS_SETTINGS] （int型に変換）
        settings['NUM_GAMES_PER_PLAYER'] = config.getint('ANALYSIS_SETTINGS', 'NUM_GAMES_PER_PLAYER')
        settings['NUM_TARGET_PLAYER'] = config.getint('ANALYSIS_SETTINGS', 'NUM_TARGET_PLAYER')
        
    except configparser.Error as e:
        print(f" 設定ファイル'{file_path}'の読み込みエラー: {e}")
        raise
        
    return settings

###########
### 関係を調べてランク推定を行う関数
###########
def run_estimate(evaluation_endpoint_move, threshold, configs):
    # 定数の表示
    print("----------------------------------------------------")
    print("パラメータ設定:")
    print(f"関係を導くためのCSVがあるディレクトリ: {configs['DATA_RELATION_DIR']}")
    print(f"ランクを推定するためのCSVがあるディレクトリ: {configs['DATA_ESTIMATION_DIR']}")
    print(f"関係を記録するCSVのディレクトリ: {configs['RESULT_RELATION_DIR']}")
    print(f"推定結果を記録するCSVのディレクトリ: {configs['RESULT_ESTIMATION_DIR']}")
    print(f"詳細結果: {configs['DETAILS_DIR']}")
    print(f"評価終点手数: {evaluation_endpoint_move}")
    print(f"修正Zスコアの閾値(τ): {threshold}")
    print(f"プレイヤーごとの棋譜数: {configs['NUM_GAMES_PER_PLAYER']}")
    print(f"棋譜数を満たすプレイヤー数: {configs['NUM_TARGET_PLAYER']}")
    print("----------------------------------------------------\n")

    # ランクの関係を導く
    print("=== ランクと平均損失の関係を導く ===")
    COEFF_A, COEFF_B = derive_relation(
        configs['DATA_RELATION_DIR'], 
        configs['RESULT_RELATION_DIR'],
        evaluation_endpoint_move,
        threshold
    )

    # ランクを推定する
    print("=== ランクを推定する ===")
    rmse = estimate_rank(
        configs['DATA_ESTIMATION_DIR'], 
        configs['RESULT_ESTIMATION_DIR'], 
        evaluation_endpoint_move,
        threshold,  
        configs['NUM_GAMES_PER_PLAYER'], 
        configs['NUM_TARGET_PLAYER'],
        COEFF_A,
        COEFF_B
    )
    return rmse

###########
### メイン関数
###########
def main():
    configs = load_config()
    EEM_RANGES = configs['EEM_LIST']
    THRESHOLD_RANGES = configs['THRESHOLD_LIST']
    DETAILS_DIR = configs['DETAILS_DIR']

    all_rmse = []
    
    print(f"手数リスト: {EEM_RANGES}")
    print(f"閾値リスト: {THRESHOLD_RANGES}")

    # 手数と閾値で2重ループ
    for evaluation_endpoint_move in EEM_RANGES:
        for threshold in THRESHOLD_RANGES:
            print(f"--- EEM: {evaluation_endpoint_move:0>3}, τ: {threshold} ---")

            # 出力をテキストファイルに切り替える
            original_stdout = sys.stdout

            try:
                # 詳細フォルダがなければ作成
                if (not os.path.exists(DETAILS_DIR)):
                    os.makedirs(DETAILS_DIR)

                threshold_str = str(int(threshold * 10))
                text_name = f"Estimate_EEM-{evaluation_endpoint_move:0>3}_TAU-{threshold_str}.txt"
                text_path = os.path.join(DETAILS_DIR, text_name)
                with open(text_path, 'w', encoding='utf-8') as f:
                    
                    # 標準出力の行き先をファイルオブジェクト f に変更
                    sys.stdout = f
                    
                    # 推定を実行
                    rmse = run_estimate(evaluation_endpoint_move, threshold, configs)

                    # 結果をリストに追加
                    all_rmse.append({
                        'EEM': evaluation_endpoint_move,
                        'Threshold': threshold,
                        'RMSE': rmse
                    })
                
            except Exception as e:
                print(f"エラー: {e}")
                
            finally:
                # 出力を画面に戻す
                sys.stdout = original_stdout

    export_rmse(all_rmse, configs)


if __name__ == '__main__':
    print("=== 推定開始 ===")
    main()
    print("=== 推定終了 ===")
    