# /**
#  * config.py
#  * パラメータと定数を定義するファイル
#  */
import os

###########
### システムのコアとなる設定値、パスを保持するクラス
###########
class Config:
    # === KataGo関連の設定 ===
    # KataGoのモデルファイル(AIの頭脳)
    MODEL_FILE = "/Users/satoshinarita/GradReserch/Analysis2/g170-b40c256x2-s5095420928-d1229425124.bin.gz"
    # KataGo自体へのパス
    KATAGO_PATH = "/opt/homebrew/Cellar/katago/1.16.4/bin/katago"

    # === パスの設定 (固定値) ===
    # 入力のパス
    INPUT_DIR = "../Input/SelectedKifus"
    # 出力のパス
    OUTPUT_DIR = "../Output"
    # 1手ごとの詳細な解析結果用
    DETAIL_CSV_PATH = "../Output/detail.csv"
    # 対局全体の統計結果用
    SUMMARY_CSV_PATH = "../Output/summary.csv"
    # KataGoの設定ファイル
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    CONFIG_FILE = os.path.join(SCRIPT_DIR, "analysis.cfg")
    
    # === その他のパラメータ ===
    # 最大解析手数
    MAX_MOVE_TO_ANALYSIS = 400
    # Pythonプロセス数
    NUM_PROCESSES = 2

# Configクラスのインスタンスを作成し、外部にエクスポート
config = Config()