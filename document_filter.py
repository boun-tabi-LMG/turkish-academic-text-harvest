from pathlib import Path
from shutil import copy
import pandas as pd
import numpy as np

source = "yoktez" # dergipark

if source == "dergipark":
    filename = "/media/disk/datasets/bounllm/dergipark/dergipark-090920230005/scored_stats.csv"
    folder = "/media/disk/datasets/bounllm/dergipark/dergipark-090920230005/"
    quantiles = { 0: -10000,
                    1: -3.3843811819182457,
                    2: -3.200857291463631,
                    3: -3.0716221210632337,
                    4: -2.989908663797539,
                    5: -2.934991125681051,
                    6: -2.897717750906116,
                    7: -2.870463355919635,
                    8: -2.8492109817776043,
                    9: -2.8332722749351937}
    q = 5
else:
    filename = "/media/disk/datasets/bounllm/yok-tez/yok-tez-090920230901/scored_stats.csv"
    folder = "/media/disk/datasets/bounllm/yok-tez/yok-tez-090920230901/"
    quantiles = { 0: -10000,
                    1: -3.1391882928960992,
                    2: -2.967988279064138,
                    3: -2.898238185762837,
                    4: -2.860549800668461,
                    5: -2.8367567170180448,
                    6: -2.8195231325636625,
                    7: -2.805734574758973,
                    8: -2.794483031599288,
                    9: -2.785006925885608}
    q = 2

df = pd.read_csv(filename)
drop_df = df[(df["mean_lm_score"] <= quantiles[q]) | (df["no_sents"] == 1)]

drop_files = [file.replace("_scored.csv", "_no_inline_citations.txt") for file in drop_df["file"]]
print(f"{source}: {len(drop_files)} files will be dropped from {len(df)} files")

with open(folder + "drop.txt", "w") as f:
    f.writelines("\n".join(drop_files))