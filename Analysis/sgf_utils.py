# /**
#  * sgf_utils.py
#  * SGFファイルの読み込みや座標変換など、SGF関連のユーティリティ関数
#  */

import sgf     # type:ignore
import chardet # type:ignore

###########
### SGF形式の座標(x,y) を GTP形式(col,rol) に変換する関数
###########
def sgf_to_gtp(sgf_move_coords):
    if len(sgf_move_coords) != 2:
        return 'pass'
    
    col_char = sgf_move_coords[0]
    row_char = sgf_move_coords[1]
    
    col = ord(col_char) - ord('a')
    row = ord(row_char) - ord('a')
    
    # GTP形式では'I'をスキップ
    if col >= 8: # 'i' (col=8) を超える場合
        col += 1 # 'j' (col=9) は GTPでは 'I' になるため、1つずらす

    col_gtp = chr(ord('A') + col)
    row_gtp = 19 - row # SGFはa1が左下、GTPはA1が左上。かつ座標系が逆
    
    return f"{col_gtp}{row_gtp}"

###########
### SGFファイルを読み込み、ゲーム情報を取得する関数
###########
def load_sgf_and_get_game_info(sgf_file_path):
    # ファイルの文字コードを自動で検出
    with open(sgf_file_path, 'rb') as f:
        raw_data = f.read()
        detected_encoding = chardet.detect(raw_data)['encoding']
        if detected_encoding is None:
            # 検出できなかった場合、一般的なエンコーディングを試行
            detected_encoding = 'utf-8' 
    
    # 検出された文字コードでファイルを読み込み
    with open(sgf_file_path, 'r', encoding=detected_encoding, errors='ignore') as f:
        sgf_string = f.read()
    
    # テキストを解析できる形式に変換
    collection = sgf.parse(sgf_string)
    game_tree = collection.children[0]

    # ボードサイズ・プレイヤー名・ランクを取得
    board_size = int(game_tree.root.properties.get('SZ', [19])[0])
    black_player = game_tree.root.properties.get('PB', [None])[0]
    white_player = game_tree.root.properties.get('PW', [None])[0]
    black_rank = game_tree.root.properties.get('BR', [None])[0]
    white_rank = game_tree.root.properties.get('WR', [None])[0]

    # 取得した値を返す
    return game_tree, board_size, black_player, white_player, black_rank, white_rank