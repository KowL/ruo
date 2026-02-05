import akshare as ak
import time

def test_em():
    try:
        print("Testing SH spot...")
        df_sh = ak.stock_sh_a_spot_em()
        print(f"SH success: {len(df_sh)}")
    except Exception as e:
        print(f"SH failed: {e}")

    try:
        print("Testing SZ spot...")
        df_sz = ak.stock_sz_a_spot_em()
        print(f"SZ success: {len(df_sz)}")
    except Exception as e:
        print(f"SZ failed: {e}")
        
    try:
        print("Testing BJ spot...")
        df_bj = ak.stock_bj_a_spot_em()
        print(f"BJ success: {len(df_bj)}")
    except Exception as e:
        print(f"BJ failed: {e}")

if __name__ == "__main__":
    test_em()
