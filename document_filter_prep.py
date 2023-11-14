from pathlib import Path
import pandas as pd
import numpy as np

folder = "/media/disk/datasets/bounllm/dergipark/dergipark-090920230005/scored_csv"
dest_file = "/media/disk/datasets/bounllm/dergipark/dergipark-090920230005/scored_stats.csv"
folder_path = Path(folder)
input_files = [str(f) for f in folder_path.iterdir() if f.name.endswith('.csv')]

if "yok-tez" in folder:
    mean_value = -2.587980095264413
    percent_10_value = -3.1009484613642972
else:
    mean_value = -2.5829296795119254
    percent_10_value = -3.1124112674168183

stats_df = pd.DataFrame()
for i, file in enumerate(input_files):
    if i % 1000 == 0:
        print(i, end = " ")
        stats_df.to_csv(dest_file, encoding='utf-8', index=False)
    try:
        df = pd.read_csv(file)
        stats_df.loc[i, "file"] = Path(file).name
        stats_df.loc[i, "no_sents"] = len(df)
        stats_df.loc[i, "no_tokens"] = np.sum(df["token_count"])
        stats_df.loc[i, "mean_lm_score"] = np.mean(df["lm_score_div"])
        stats_df.loc[i, "lessthan_mean"] = len(df[df["lm_score_div"] < mean_value]) / len(df) * 100
        stats_df.loc[i, "lessthan_10_percent"] = len(df[df["lm_score_div"] < percent_10_value]) / len(df) * 100
    except:
        print("Read error for", file)    
stats_df.to_csv(dest_file, encoding='utf-8', index=False)