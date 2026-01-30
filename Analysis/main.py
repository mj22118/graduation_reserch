# /**
#  * main
#  * KataGoと1手1手を比較し、悪手度を算出するプログラム
#  *
#  * Author : 成田知史
#  * Number : 221205118
# */

import multiprocessing as mp
from multiprocessing import Manager
import os
import sys
import glob
import analysis
from config import config

###########
### 並列で解析を行う関数
###########
def run_parallel_analysis():
    # SGFファイルパスのリストを取得
    sgf_files = glob.glob(os.path.join(config.INPUT_DIR, '**', '*.sgf'), recursive=True) 
    sgf_files.sort()
    if (not sgf_files):
        print(f"エラー: SGFファイル '{config.INPUT_DIR}' が見つかりません")
        sys.exit(1)
    
    # 定数の値を表示
    print("=" * 60)
    print(f"棋譜数      : {len(sgf_files)}")
    print(f"入力フォルダ: {config.INPUT_DIR}")
    print(f"出力フォルダ: {config.OUTPUT_DIR}")
    print(f"解析手数    : {config.MAX_MOVE_TO_ANALYSIS}")
    print(f"スレッド数  : {config.NUM_PROCESSES}")
    print("=" * 60 + "\n")

    # ManagerとLockの生成、並列処理の実行
    with Manager() as manager:
        # Managerを使って共有ロックオブジェクトを生成し、CSVアクセスを保護
        csv_lock = manager.Lock() 
        
        tasks = []
        for filepath in sgf_files:
            # タスクリストの構築
            tasks.append((filepath, csv_lock))

        # 解析の並列処理
        with mp.Pool(processes=config.NUM_PROCESSES) as pool:
            pool.starmap(analysis.analyze_game, tasks)
        
        print("\n--- 全ての棋譜の並列解析が完了 ---")

if __name__ == '__main__':
    run_parallel_analysis()