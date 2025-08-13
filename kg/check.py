import pandas as pd

try:
    df = pd.read_csv("faq.csv")
    print("表头：", df.columns)
    print("前几行：", df.head())
except Exception as e:
    print("pandas 读取 csv 时出错：", e)