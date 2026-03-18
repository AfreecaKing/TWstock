import sqlite3
import pandas as pd
import os


def create_table():
    """建立資料庫表格"""
    os.makedirs('./database', exist_ok=True)
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()

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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ticker_categories (
            ticker TEXT,
            category_id INTEGER,
            PRIMARY KEY (ticker, category_id),
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
        )
    ''')

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ 資料庫初始化完成")


def insert_price(data):
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
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT ticker FROM price_daily ORDER BY ticker")
    tickers = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tickers


def get_last_price_date(ticker):
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(date) FROM price_daily WHERE ticker = ?", (ticker,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result[0] else None


def delete_ticker(ticker):
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM price_daily WHERE ticker = ?", (ticker,))
        price_deleted = cursor.rowcount
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


def get_all_categories():
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cursor.fetchall()
    conn.close()
    return categories


def add_category(name):
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_category(category_id):
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
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()

    if category_id is None:
        cursor.execute("""
            SELECT DISTINCT pd.ticker, c.name as category_name
            FROM price_daily pd
            LEFT JOIN ticker_categories tc ON pd.ticker = tc.ticker
            LEFT JOIN categories c ON tc.category_id = c.id
            ORDER BY pd.ticker
        """)
    else:
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


def get_category_avg_change_5d(category_id=None):
    """取得分類內所有股票近N日的總漲跌幅平均（預設5日）"""
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()

    if category_id is None:
        cursor.execute("SELECT DISTINCT ticker FROM price_daily")
    else:
        cursor.execute("""
            SELECT DISTINCT ticker FROM ticker_categories
            WHERE category_id = ?
        """, (category_id,))

    tickers = [row[0] for row in cursor.fetchall()]
    conn.close()

    changes = []
    days = 5

    for ticker in tickers:
        conn = sqlite3.connect('database/taiwan_stock.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT close FROM price_daily
            WHERE ticker = ?
            ORDER BY date DESC
            LIMIT ?
        """, (ticker, days))
        rows = cursor.fetchall()
        conn.close()

        if len(rows) < days:
            continue

        closes = [r[0] for r in rows]  # 最新在前
        change = (closes[0] - closes[-1]) / closes[-1] * 100
        changes.append(change)

    return sum(changes) / len(changes) if changes else None


def get_all_categories_avg_change(days=5):
    """
    取得所有分類的漲跌幅平均，用於比較圖表。
    days: 計算天數（最新一天 vs N天前）
    """
    conn = sqlite3.connect('database/taiwan_stock.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM categories ORDER BY name")
    categories = cursor.fetchall()
    conn.close()

    results = []
    for cat_id, cat_name in categories:
        conn = sqlite3.connect('database/taiwan_stock.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT ticker FROM ticker_categories
            WHERE category_id = ?
        """, (cat_id,))
        tickers = [row[0] for row in cursor.fetchall()]
        conn.close()

        if not tickers:
            continue

        changes = []
        for ticker in tickers:
            conn = sqlite3.connect('database/taiwan_stock.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT close FROM price_daily
                WHERE ticker = ?
                ORDER BY date DESC
                LIMIT ?
            """, (ticker, days))
            rows = cursor.fetchall()
            conn.close()

            if len(rows) < days:
                continue

            closes = [r[0] for r in rows]  # 最新在前
            change = (closes[0] - closes[-1]) / closes[-1] * 100
            changes.append(change)

        if changes:
            results.append({
                'id': cat_id,
                'name': cat_name,
                'avg_change': sum(changes) / len(changes),
                'ticker_count': len(tickers)
            })

    results.sort(key=lambda x: x['avg_change'], reverse=True)
    return results