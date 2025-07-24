import akshare as ak
import pandas as pd



def get_lhb_data(date: str) -> pd.DataFrame:
    df = ak.stock_lhb_detail_em(date, date)
    return df


df = get_lhb_data("20250724")
print(df.head())  # 输出DataFrame：包含序号、代码、名称、解读、价格、换手、流通市值等列
