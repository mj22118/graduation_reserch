# /**
#  * export_rmse.py
#  * RMSEをパラメータごとに出力する
# */

import pandas as pd

###########
### 全RMSEをCSVファイルに出力する関数
###########
def export_to_csv(all_rmse, configs):
    # データの準備
    df = pd.DataFrame(all_rmse)
    pivot_df = df.pivot(index='EEM', columns='Threshold', values='RMSE') # ピボット作成
    filename = configs['RESULT_RMSE_CSV']
    eem_list = configs['EEM_LIST']
    thresh_list = configs['THRESHOLD_LIST']
    pivot_df = pivot_df.reindex(index=eem_list, columns=thresh_list) # データを2次元表に
    
    # CSVとして保存
    # index=TrueでEEMを出力。ヘッダーにはThresholdが並ぶ
    pivot_df.to_csv(filename, index=True, encoding='utf-8')

###########
### 全RMSEをテキストファイルに出力する関数
###########
def export_to_text(all_rmse, configs):
    # データの準備
    df = pd.DataFrame(all_rmse)
    pivot_df = df.pivot(index='EEM', columns='Threshold', values='RMSE')
    filename = configs['RESULT_RMSE_TEXT']
    eem_list = configs['EEM_LIST']
    thresh_list = configs['THRESHOLD_LIST']

    with open(filename, "w", encoding="utf-8") as f:
        # 定数の表示
        f.write("----------------------------------------------------\n")
        f.write("パラメータ設定:\n")
        f.write(f"関係を導くためのCSVがあるディレクトリ: {configs['DATA_RELATION_DIR']}\n")
        f.write(f"ランクを推定するためのCSVがあるディレクトリ: {configs['DATA_ESTIMATION_DIR']}\n")
        f.write(f"関係を記録するCSVのディレクトリ: {configs['RESULT_RELATION_DIR']}\n")
        f.write(f"推定結果を記録するCSVのディレクトリ: {configs['RESULT_ESTIMATION_DIR']}\n")
        f.write(f"詳細結果: {configs['DETAILS_DIR']}\n")
        f.write(f"プレイヤーごとの棋譜数: {configs['NUM_GAMES_PER_PLAYER']}\n") 
        f.write(f"棋譜数を満たすプレイヤー数: {configs['NUM_TARGET_PLAYER']}\n")
        f.write("----------------------------------------------------\n\n")

        # 表のヘッダの書込み
        f.write("=== ランク推定精度(RMSE) 網羅的探索結果 ===\n\n")
        f.write("[ 行: EEM(T_max) / 列: 閾値(τ) ]\n")
        header = "|#####||" + "".join([f"  {t:1.1f}  |" for t in thresh_list])
        line_len = len(header)
        border = "+" + "-" * (line_len - 2) + "+"
        f.write(border + "\n")
        f.write(header + "\n")
        f.write("+=====++" + "=======+" * len(thresh_list) + "\n")

        # データ行の書き込み (EEM_LISTの順にループ)
        for eem in eem_list:
            if eem not in pivot_df.index: continue
            
            row_str = f"| {eem:3d} ||"
            for t in thresh_list:
                if (t in pivot_df.columns):
                    val = pivot_df.loc[eem, t]
                    row_str += f" {val:5.3f} |" if pd.notna(val) else "  None   |"
                else:
                    row_str += "  None   |"
            f.write(row_str + "\n")
            f.write("+-----++" + "-------+" * len(thresh_list) + "\n")

        # 最良値の特定
        if (not df.empty):
            best = df.loc[df['RMSE'].idxmin()]
            f.write(f"\nBEST: EEM={int(best['EEM'])}, τ={best['Threshold']} -> RMSE={best['RMSE']}\n")

###########
### 全RMSEをコンソールに出力する関数
###########
def export_to_console(all_rmse):
    print("\n" + "-"*20)
    print(f"EEM |  τ  | RMSE")
    print("-" * 20)

    for entry in all_rmse:
        eem = entry['EEM']
        thresh = entry['Threshold']
        rmse = entry['RMSE']
        if rmse is not None:
            print(f"{eem:3d} | {thresh:1.1f} | {rmse}")

    # 最良値の特定
    valid_results = [r for r in all_rmse if r['RMSE'] is not None]
    if valid_results:
        best = min(valid_results, key=lambda x: x['RMSE'])
        print("-"*20)
        print(f"BEST: EEM={best['EEM']}, τ={best['Threshold']} -> RMSE={best['RMSE']} \n")

###########
### 全RMSEを出力する関数
###########
def export_rmse(all_rmse, configs):
    export_to_csv(all_rmse, configs)
    export_to_text(all_rmse, configs)
    export_to_console(all_rmse)
    