# /**
#  * select_kifu
#  * モデル構築フェーズにてランクごとに棋譜を抽出する
#  *
#  * Author : 成田知史
#  * Number : 221205118
# */

import os
import shutil
import sys
import random
import re # 正規表現：文字列のパターンマッチング・検索・置換を行う

###########
### 設定
###########
SRC_DIR = None # 入力元ディレクトリ; source
DST_DIR = None # 出力先ディレクトリ; destination
MIN_MOVES = None 
NUM_GAMES_TO_COPY = None
# 段級位のリスト。弱い順に並べることで、インデックスがそのまま強さの順序を表す
RANK_ORDER = [
    '30级', '29级', '28级', '27级', '26级', '25级', '24级', '23级', '22级', '21级', 
    '20级', '19级', '18级', '17级', '16级', '15级', '14级', '13级', '12级', '11级',
    '10级', '9级', '8级', '7级', '6级', '5级', '4级', '3级', '2级', '1级',
    '1段', '2段', '3段', '4段', '5段', '6段', '7段', '8段', '9段',
    '1プロ', '2プロ', '3プロ', '4プロ', '5プロ', '6プロ', '7プロ', '8プロ', '9プロ',
]

###########
### 段級位文字列を整数に変換して返す関数
### 例) '30级' -> 0
###########
def get_rank_as_int(rank_str):
    try:
        # 正規化されたリスト内を直接検索
        return RANK_ORDER.index(rank_str)
    except ValueError:
        return None

###########
### 条件に合致するSGFファイルを収集する関数
###########
def collect_game_data():
    valid_sgf_files = [] # 条件に合致するSGFファイル
    
    # SFGファイルを探索
    print("SGFファイルを検索")
    for root, _, files in os.walk(SRC_DIR): # ソースフォルダを探索する
        for file in files: # ファイルを1つずつ取り出す
            if (file.endswith('.sgf')): # 拡張子が .sgf のもの
                file_path = os.path.join(root, file) # ファイルのパスを構築
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read() # ファイルのデータを文字列で読み取る

                        # 手数 ('B[' または 'W[' の出現回数) を数える
                        num_moves = len(re.findall(r'[BW]\[[a-z]{2}\]', content))

                        # 段級位の抽出
                        black_rank_str = re.search(r'BR\[(.*?)\]', content)
                        white_rank_str = re.search(r'WR\[(.*?)\]', content)
                        
                        # RANK_ORDERのリストのインデックスに変換
                        black_rank_int = get_rank_as_int(black_rank_str.group(1))
                        white_rank_int = get_rank_as_int(white_rank_str.group(1))
                        
                        # 指定する条件; 級段位が同じ かつ 100手以上
                        if ((black_rank_int != None) and (white_rank_int != None) 
                            and (abs(black_rank_int - white_rank_int) == 0)
                            and (num_moves >= MIN_MOVES)):
                            valid_sgf_files.append(file_path)
                                                
                except Exception as e:
                    print(f"ファイル {file_path} の解析中にエラーが発生しました: {e}")
                    continue

    print(f"条件に合致した棋譜の総数: {len(valid_sgf_files)} 局\n")

    return valid_sgf_files

###########
### ランダムに指定数の棋譜を抽出する関数
###########
def select_games(valid_sgf_files):
    files_to_copy = []
    ### 抽出する棋譜を選択 
    if (len(valid_sgf_files) <= NUM_GAMES_TO_COPY): # 条件を満たす棋譜が指定数以下の場合
        files_to_copy = valid_sgf_files
        print(f"棋譜 ({len(files_to_copy)} 局) を選択\n")
    else:
        # 条件を満たす棋譜をランダムに指定数選択
        files_to_copy = random.sample(valid_sgf_files, k=NUM_GAMES_TO_COPY)
        print(f"{len(files_to_copy)} 局の棋譜を選択\n")

    files_to_copy.sort()
    return files_to_copy

###########
### 選択した棋譜をコピーする関数
###########
def copy_selected_files(files_to_copy):
    ### 選択した棋譜をコピー
    for file_path in files_to_copy:
        file_name = os.path.basename(file_path) # パスからファイル名を取得
        destination_path = os.path.join(DST_DIR, file_name) # コピー先パスの生成
        
        try:
            shutil.copy(file_path, destination_path) # ファイルのコピー
            print(f"コピー完了: {file_name}")
        except Exception as e:
            print(f"ファイル {file_name} のコピー中にエラーが発生しました: {e}")

###########
### メイン関数
###########
def main():
    valid_sgf_files = [] # 条件を満たすSGFファイル
    files_to_copy = []   # コピーする棋譜ファイル

    print("<抽出開始>\n")

    # 条件に合致するSGFファイルを収集する
    valid_sgf_files = collect_game_data()

    # ランダムに指定数の棋譜を抽出する
    files_to_copy = select_games(valid_sgf_files)

    # 選択した棋譜をコピーする
    copy_selected_files(files_to_copy)

    print("\n<抽出完了>")

if __name__ == "__main__":
    if (len(sys.argv) < 5): # 引数が4つない場合
        print("エラー: 引数が不足しています。")
        sys.exit(1)

    # 引数をグローバル定数に設定
    SRC_DIR = sys.argv[1] # 入力元ディレクトリ; source
    DST_DIR = sys.argv[2] # 出力先ディレクトリ; destination 
    NUM_GAMES_TO_COPY = int(sys.argv[3]) # 抽出する棋譜数
    MIN_MOVES = int(sys.argv[4]) # 最低手数

    # グローバル定数を表示
    print("----------------------------------------------------")
    print("パラメータ設定")
    print(f"抽出する段位: {SRC_DIR}")
    print(f"出力フォルダ: {DST_DIR}")
    print(f"抽出する棋譜数: {NUM_GAMES_TO_COPY}")
    print(f"最低手数: {MIN_MOVES}")
    print("----------------------------------------------------\n")

    main()