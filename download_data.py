import yfinance as yf
import database as db
from datetime import datetime, timedelta


def insert_ticker(ticker, silent=False):
    """
    新增股票並抓取歷史資料
    ticker: 股票代碼，例如 "2330.TW"
    silent: 是否靜默模式（用於自動重試時不顯示錯誤）
    """
    if not silent:
        print(f"🔄 正在抓取 {ticker} 的歷史資料...")
    
    try:
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(period="max")
        
        if df.empty:
            if not silent:
                print(f"⚠️ {ticker} 查無資料")
            return False
            
        df = df.reset_index()
        df['ticker'] = ticker
        
        # 重新命名欄位
        df = df.rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume',
            'Dividends': 'dividends',
            'Stock Splits': 'stock_splits'
        })
        
        # 選擇需要的欄位
        df = df[['date', 'open', 'high', 'low', 'close',
                 'volume', 'dividends', 'stock_splits', 'ticker']]
        
        # 格式化日期
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        
        # 數值處理：價格四捨五入到兩位小數，成交量轉整數
        price_cols = ['open', 'high', 'low', 'close', 'dividends', 'stock_splits']
        df[price_cols] = df[price_cols].round(2)
        df['volume'] = df['volume'].astype(int)
        
        # 存入資料庫
        db.insert_price(df)
        if not silent:
            print(f"✅ {ticker} 新增成功，共 {len(df)} 筆歷史資料")
        return True
        
    except Exception as e:
        if not silent:
            print(f"❌ {ticker} 新增失敗：{e}")
        return False


def update_all_ticker():
    """
    更新所有股票的價格資料（僅抓取新資料）
    """
    tickers = db.get_all_tickers()
    print(f"\n{'='*60}")
    print(f"📈 開始更新 {len(tickers)} 支股票")
    print(f"{'='*60}\n")
    
    success_count = 0
    fail_count = 0
    already_updated = 0
    
    for i, ticker in enumerate(tickers, 1):
        try:
            print(f"[{i}/{len(tickers)}] 🔄 更新 {ticker}...", end=" ")
            
            # 取得最後更新日期
            last_date = db.get_last_price_date(ticker)
            
            ticker_obj = yf.Ticker(ticker)
            
            # 如果有最後日期，只抓取之後的資料
            if last_date:
                # 從最後日期的隔天開始抓
                start_date = (datetime.strptime(last_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
                df = ticker_obj.history(start=start_date)
                
                if df.empty:
                    print("✓ 已是最新資料")
                    already_updated += 1
                    continue
                    
                print(f"📥 新增 {len(df)} 筆資料", end=" ")
            else:
                # 沒有歷史資料，抓全部
                df = ticker_obj.history(period="max")
                print(f"📥 抓取 {len(df)} 筆資料（完整歷史）", end=" ")
            
            if df.empty:
                print("⚠️ 無可用資料")
                fail_count += 1
                continue

            # 處理資料格式
            df = df.reset_index()
            df['ticker'] = ticker

            df = df.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume',
                'Dividends': 'dividends',
                'Stock Splits': 'stock_splits'
            })

            df = df[['date', 'open', 'high', 'low', 'close',
                     'volume', 'dividends', 'stock_splits', 'ticker']]
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            
            # 數值處理
            price_cols = ['open', 'high', 'low', 'close', 'dividends', 'stock_splits']
            df[price_cols] = df[price_cols].round(2)
            df['volume'] = df['volume'].astype(int)

            # 存入資料庫
            db.insert_price(df)
            
            print("✅")
            success_count += 1
            
        except Exception as e:
            print(f"❌ 錯誤: {e}")
            fail_count += 1
    
    print(f"\n{'='*60}")
    print(f"📊 更新完成統計:")
    print(f"   ✅ 成功更新: {success_count}/{len(tickers)}")
    print(f"   ✓  已是最新: {already_updated}/{len(tickers)}")
    print(f"   ❌ 更新失敗: {fail_count}/{len(tickers)}")
    print(f"{'='*60}\n")


def get_ticker_info(ticker):
    """
    取得股票基本資訊（選用功能）
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        info = ticker_obj.info
        
        # 取得中文名稱（如果有的話）
        name = info.get('longName', ticker)
        sector = info.get('sector', '未知')
        industry = info.get('industry', '未知')
        
        print(f"\n股票資訊：")
        print(f"  代碼：{ticker}")
        print(f"  名稱：{name}")
        print(f"  產業：{sector}")
        print(f"  行業：{industry}")
        
        return info
        
    except Exception as e:
        print(f"❌ 無法取得 {ticker} 的資訊：{e}")
        return None
