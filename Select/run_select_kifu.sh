#!/bin/bash

# 条件に合う棋譜を選択するシェルファイル
# Creator: SatoshiNarita; 221205118

# Pythonのエンコーディング設定 (環境変数として設定)
export PYTHONIOENCODING="utf-8"

# === パラメータ ===
# 使用するプログラムのモード
MODE="1"
# 入力元ディレクトリ
RANK_LIST=("12k" "3k" "7d")
# 出力先ディレクトリ
DST_DIR="SelectedKifus"
# 抽出する棋譜数(1)
NUM_GAMES_TO_COPY="100"
# 抽出するプレイヤー数(2)
NUM_PLAYERS_TO_COPY="5"
# プレイヤーごとに抽出する棋譜ファイル数(2)
NUM_GAMES_PER_PLAYER="10"
# 最低手数(1,2)
MIN_MOVES="100"
# ランクから棋譜を抽出するプログラム名(1)
GAME_BASE_SCRIPT="select_kifu_by_games.py"
# プレイヤーから棋譜を抽出するプログラム名(2)
PLAYER_BASE_SCRIPT="select_kifu_by_players.py"

# === 出力ファイルを作成 ===
# 今日の日付を取得（YYYYMMDD形式）
TODAY_DATE_STR=$(date +%Y%m%d)
# 結果を保存するtxtファイル名
OUTPUT_FILE="../Output/SelectKifu_${TODAY_DATE_STR}_${SRC_RANK}.txt"

# === 確認画面の表示 ===
if [ "$MODE" == "1" ]; then
    echo "----------------------------------------------------"
    echo "ランクから棋譜を抽出する_1"
    echo "----------------------------------------------------"
    echo "パラメータ設定"
    echo "抽出する段位: ${RANK_LIST[@]}"
    echo "出力フォルダ: $DST_DIR"
    echo "抽出する棋譜数: $NUM_GAMES_TO_COPY"
    echo "最低手数: $MIN_MOVES"
    echo "----------------------------------------------------"
    echo ""
elif [ "$MODE" == "2" ]; then
    echo "----------------------------------------------------"
    echo "プレイヤーから棋譜を抽出する_2"
    echo "----------------------------------------------------"
    echo "パラメータ設定"
    echo "抽出する段位: ${RANK_LIST[@]}"
    echo "出力フォルダ: $DST_DIR"
    echo "抽出するプレイヤー数: $NUM_PLAYERS_TO_COPY"
    echo "プレイヤーごとに抽出する棋譜ファイル数: $NUM_GAMES_PER_PLAYER"
    echo "最低手数: $MIN_MOVES"
    echo "----------------------------------------------------"
    echo ""    
else
    echo "エラー: 不正な実行モード $MODE" >&2
fi

# === プログラムの実行 ===
for SRC_RANK in "${RANK_LIST[@]}"; do
    OUTPUT_FILE="../Output/SelectKifu_${TODAY_DATE_STR}_${SRC_RANK}.txt"
    if [ "$MODE" == "1" ]; then
        echo "--- 抽出する段位: $SRC_RANK ---"
        python3 "$GAME_BASE_SCRIPT" "./$SRC_RANK" "./$DST_DIR" "$NUM_GAMES_TO_COPY" "$MIN_MOVES" > "$OUTPUT_FILE"

    elif [ "$MODE" == "2" ]; then
        echo "--- 抽出する段位: $SRC_RANK ---"
        python3 "$PLAYER_BASE_SCRIPT" "./$SRC_RANK" "./$DST_DIR" "$NUM_PLAYERS_TO_COPY" "$NUM_GAMES_PER_PLAYER" "$MIN_MOVES" > "$OUTPUT_FILE"

    else
        echo "エラー: 不正な実行モード" >&2  # エラーメッセージを標準エラー出力へ
        exit 1
    fi
    echo "--- 結果は \"$OUTPUT_FILE\" に保存 ---"
    echo ""
done

echo "--- 抽出完了 ---"
read -r -p "続行するにはEnterキーを押してください..."