# /**
#  * select_kifu_by_players
#  * モデル評価フェーズにてプレイヤーごとに棋譜を抽出する
#  *
#  * Author : 成田知史
#  * Number : 221205118
# */

import os
import shutil
import sys
import random
import re # 正規表現：文字列のパターンマッチング・検索・置換を行う
from collections import Counter, defaultdict # 要素の出現回数を辞書形式で管理する

###########
### 定数(一部はbatファイルで指定)
###########
SRC_DIR = None # 入力元ディレクトリ; source
DST_DIR = None  # 出力先ディレクトリ; destination
MIN_MOVES = None
NUM_PLAYERS_TO_COPY = None # 抽出するプレイヤー数
NUM_GAMES_PER_PLAYER = None # プレイヤーごとに抽出する棋譜ファイル数

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
### SGFファイルを走査し、プレイヤーごとに出現回数と棋譜のパスを収集する
###########
def collect_player_data():
    player_counts = Counter()
    player_games = defaultdict(list)
    valid_players = []

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

                        # プレイヤー名を取得
                        players = []
                        black_player = re.search(r'PB\[(.*?)\]', content)
                        white_player = re.search(r'PW\[(.*?)\]', content)

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
                            # 取得したプレイヤー名をリストに追加
                            players.append(black_player.group(1))
                            players.append(white_player.group(1))
                            player_counts.update(players)
                            for player in players:
                                player_games[player].append(file_path)
                                                
                except Exception as e:
                    print(f"ファイル {file_path} の解析中にエラーが発生しました: {e}")
                    continue

    # プレイヤーの出現回数が指定回数以上のものを選択
    for player,count in player_counts.items():
        if (count >= NUM_GAMES_PER_PLAYER):
            valid_players.append(player)

    print(f"条件に合致したプレイヤーの総数: {len(valid_players)} 人 \n")
    return valid_players, player_games

###########
### 条件に合うプレイヤーから選出し、それぞれのプレイヤーから指定数の棋譜を抽出する
###########
def select_games(valid_players, player_games):
    files_to_copy = []
    # 条件を満たす棋譜が指定数以下の場合
    if (len(valid_players) <= NUM_PLAYERS_TO_COPY): 
        players_to_copy = valid_players # 全選択
    else:
        # 条件を満たすプレイヤーをランダムに指定数選択
        players_to_copy = random.sample(valid_players, k=NUM_PLAYERS_TO_COPY)
    print(f"プレイヤー ({len(players_to_copy)} 人) を選択\n")

    # 棋譜を抽出するプレイヤーを表示
    for player in players_to_copy:
        # 文字化けしたプレイヤー名を強制的に戻す
        encoded_player = (player.encode('cp1252', errors='ignore')).decode('utf-8', errors='ignore')
        print(f"{player} ({encoded_player})")
    
    # 選択された各プレイヤーから、指定された数の棋譜を抽出
    for player in players_to_copy:
        player_game_list = player_games[player]
        selected_games = random.sample(player_game_list, k=NUM_GAMES_PER_PLAYER)
        files_to_copy.extend(selected_games)
        selected_games.sort()
        # プレイヤー名と棋譜を表示
        print("\n" + player)
        for i in selected_games:
            print(f"  {i}")
    print(f"\n最終的に選択された棋譜の総数: {len(files_to_copy)} 局 \n")
    return files_to_copy

###########
### 選択した棋譜をコピーする関数
###########
def copy_selected_files(files_to_copy):
    for file_path in files_to_copy:
        file_name = os.path.basename(file_path) # パスからファイル名を取得
        destination_path = os.path.join(DST_DIR, file_name) # コピー先パスの生成
        
        try:
            shutil.copy(file_path, destination_path) # ファイルのコピー
            print(f"コピー完了: {file_name}")
        except Exception as e:
            print(f"ファイル {file_name} のコピー中にエラーが発生しました: {e}")
    print("全員分のコピーが完了\n")    

###########
### メイン関数
###########
def main():
    valid_players = [] # 出現回数を満たすプレイヤー
    player_games = [] # プレイヤー名と棋譜のリスト
    files_to_copy = [] # コピーする棋譜ファイル
    
    print("<抽出開始>\n")

    ### SFGファイルを探索
    valid_players, player_games = collect_player_data()

    ### 抽出する棋譜を選択 
    files_to_copy = select_games(valid_players, player_games)
       
    ### 選択した棋譜をコピー
    copy_selected_files(files_to_copy)

    print("<抽出完了>\n")

if __name__ == '__main__':
    if (len(sys.argv) < 6): # 引数が5つない場合
        print("エラー: 引数が不足しています。")
        sys.exit(1)

    # 引数をグローバル定数に設定
    SRC_DIR = sys.argv[1] # 入力元ディレクトリ; source
    DST_DIR = sys.argv[2] # 出力先ディレクトリ; destination
    NUM_PLAYERS_TO_COPY = int(sys.argv[3]) # 抽出するプレイヤー数
    NUM_GAMES_PER_PLAYER = int(sys.argv[4]) # プレイヤーごとに抽出する棋譜ファイル数
    MIN_MOVES = int(sys.argv[5]) # 最低手数

    # グローバル定数を表示
    print("----------------------------------------------------")
    print("パラメータ設定")
    print(f"抽出する段位: {SRC_DIR}")
    print(f"出力フォルダ: {DST_DIR}")
    print(f"抽出するプレイヤー数: {NUM_PLAYERS_TO_COPY}")
    print(f"プレイヤーごとに抽出する棋譜ファイル数: {NUM_GAMES_PER_PLAYER}")
    print(f"最短手数: {MIN_MOVES}")
    print("----------------------------------------------------\n")

    main()
