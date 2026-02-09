import sys
import os
import logging

# Add backend to path to allow imports from app
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from app.services.market_data import MarketDataService

def test_xq_price():
    import akshare as ak
    print("\n>>> Debugging AkShare output directly (stock_individual_spot_xq)...")
    try:
        df = ak.stock_individual_spot_xq(symbol="SH600519")
        with open("tests/ak_output.txt", "w") as f:
            f.write(f"Columns: {df.columns}\n")
            f.write(f"Data:\n{df}\n")
        print("Data written to tests/ak_output.txt")
    except Exception as e:
        print(f"AkShare Error: {e}")

    service = MarketDataService()
    
    test_symbols = ["000001", "600519", "300059"] # Ping An Bank, Moutai, East Money
    
    print("\n>>> Starting test for get_stock_price_xq...")
    
    for symbol in test_symbols:
        print(f"\nTesting symbol: {symbol}")
        try:
            price = service.get_stock_price_xq(symbol)
            print(f"Symbol: {symbol}, Price: {price}")
        except Exception as e:
            print(f"Error for {symbol}: {e}")

if __name__ == "__main__":
    test_xq_price()
