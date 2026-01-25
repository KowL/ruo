import akshare as ak

stock_zh_a_hist_df = ak.stock_zh_a_hist(
    symbol="600734",
    period="daily",
    start_date="20050501",
    end_date="20050520",
    adjust="hfq"
)
print(stock_zh_a_hist_df)

stock_news_em_df = ak.stock_news_em(symbol="603777")
print(stock_news_em_df)

