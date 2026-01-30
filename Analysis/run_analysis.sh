#!/bin/bash

# 棋譜ファイルの解析をするシェルスクリプト
# Creator: SatoshiNarita; 221205118

# === 設定 ===
# 解析プログラム名
SCRIPT_NAME="main.py"
# 結果を送信するプログラム
SEND_SCRIPT="send_result.py"

# === Pythonで解析 ===
python3 "$SCRIPT_NAME"

# === 実行結果の確認 ===
echo ""
echo "--- 全てのファイルの解析が完了 ---"

# === PCをスリープ状態に移行 ===
echo ""
echo "--- スリープ状態に入る ---"
osascript -e 'tell application "System Events" to sleep'