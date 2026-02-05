import sqlite3
import pandas as pd
import os


def create_table():
    """建立資料庫表格"""
    os.makedirs('./database', exist_ok=True)
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()

    # 股價日線表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_daily (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            dividends REAL,
            stock_splits REAL,
            ticker TEXT,
            UNIQUE (ticker, date)
        )
    ''')

    # 分類表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')

    # 股票分類對應表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ticker_categories (
            ticker TEXT,
            category_id INTEGER,
            PRIMARY KEY (ticker, category_id),
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
        )
    ''')

    # 不設定預設分類，讓用戶自己建立
    conn.commit()
    cursor.close()
    conn.close()
    print("✅ 資料庫初始化完成")


def insert_price(data):
    """
    新增或更新股價資料
    data: DataFrame 包含 date, open, high, low, close, volume, dividends, stock_splits, ticker
    """
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()
    
    sql = """
    INSERT INTO price_daily (
        date, open, high, low, close, volume, dividends, stock_splits, ticker
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(ticker, date)
    DO UPDATE SET
        open = excluded.open,
        high = excluded.high,
        low = excluded.low,
        close = excluded.close,
        volume = excluded.volume,
        dividends = excluded.dividends,
        stock_splits = excluded.stock_splits;
    """
    
    data_to_insert = list(data.itertuples(index=False, name=None))
    cursor.executemany(sql, data_to_insert)
    conn.commit()
    conn.close()


def select_price(ticker):
    """
    查詢指定股票的價格資料
    回傳 DataFrame
    """
    conn = sqlite3.connect('database/taiwan_stock.db')
    try:
        sql = """
        SELECT date, open, high, low, close, volume, dividends, stock_splits
        FROM price_daily
        WHERE ticker = ?
        ORDER BY date
        """
        df = pd.read_sql_query(sql, conn, params=(ticker,))
        df['date'] = pd.to_datetime(df['date'])
        return df
    finally:
        conn.close()


def get_all_tickers():
    """取得所有股票代碼"""
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT ticker
        FROM price_daily
        ORDER BY ticker
    """)
    tickers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tickers


def get_last_price_date(ticker):
    """取得指定股票的最後價格日期"""
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT MAX(date)
        FROM price_daily
        WHERE ticker = ?
    """, (ticker,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result[0] else None


def delete_ticker(ticker):
    """刪除指定股票的所有資料"""
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()
    try:
        # 刪除股價資料
        cursor.execute("DELETE FROM price_daily WHERE ticker = ?", (ticker,))
        price_deleted = cursor.rowcount

        # 刪除分類關聯
        cursor.execute("DELETE FROM ticker_categories WHERE ticker = ?", (ticker,))
        category_deleted = cursor.rowcount

        conn.commit()
        print(f"🗑️ {ticker} 已刪除 | 股價資料: {price_deleted} 筆, 分類關聯: {category_deleted} 筆")
        return price_deleted > 0
    except sqlite3.Error as e:
        print("❌ 刪除失敗：", e)
        return False
    finally:
        conn.close()


# ========== 分類管理功能 ==========

def get_all_categories():
    """取得所有分類"""
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cursor.fetchall()
    conn.close()
    return categories


def add_category(name):
    """新增分類"""
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # 分類已存在
    finally:
        conn.close()


def delete_category(category_id):
    """刪除分類（會自動刪除相關的股票-分類關聯）"""
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def assign_ticker_to_category(ticker, category_id):
    """將股票指定到分類"""
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO ticker_categories (ticker, category_id)
            VALUES (?, ?)
        """, (ticker, category_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def remove_ticker_from_category(ticker, category_id):
    """將股票從分類中移除"""
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()
    try:
        cursor.execute("""
            DELETE FROM ticker_categories
            WHERE ticker = ? AND category_id = ?
        """, (ticker, category_id))
        conn.commit()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()


def get_ticker_categories(ticker):
    """取得股票所屬的所有分類"""
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.name
        FROM categories c
        JOIN ticker_categories tc ON c.id = tc.category_id
        WHERE tc.ticker = ?
        ORDER BY c.name
    """, (ticker,))
    categories = cursor.fetchall()
    conn.close()
    return categories


def get_tickers_by_category(category_id=None):
    """
    取得分類下的所有股票
    如果 category_id 為 None，回傳所有股票及其分類
    """
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()

    if category_id is None:
        # 取得所有股票及其分類
        cursor.execute("""
            SELECT DISTINCT pd.ticker, c.name as category_name
            FROM price_daily pd
            LEFT JOIN ticker_categories tc ON pd.ticker = tc.ticker
            LEFT JOIN categories c ON tc.category_id = c.id
            ORDER BY pd.ticker
        """)
    else:
        # 取得特定分類下的股票
        cursor.execute("""
            SELECT DISTINCT pd.ticker
            FROM price_daily pd
            JOIN ticker_categories tc ON pd.ticker = tc.ticker
            WHERE tc.category_id = ?
            ORDER BY pd.ticker
        """, (category_id,))

    result = cursor.fetchall()
    conn.close()
    return result


def get_ticker_statistics(ticker):
    """
    取得股票統計資訊（選用功能）
    """
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_days,
            MIN(date) as first_date,
            MAX(date) as last_date,
            MIN(low) as lowest_price,
            MAX(high) as highest_price,
            AVG(close) as avg_price,
            SUM(volume) as total_volume
        FROM price_daily
        WHERE ticker = ?
    """, (ticker,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'total_days': result[0],
            'first_date': result[1],
            'last_date': result[2],
            'lowest_price': result[3],
            'highest_price': result[4],
            'avg_price': result[5],
            'total_volume': result[6]
        }
    return None
