import akshare as ak

print("Searching for Xueqiu related functions in akshare:")
for attr in dir(ak):
    if "xq" in attr and "stock" in attr:
        print(attr)
