import mysql.connector

# 1. 建立資料庫連線設定
try:
    connection = mysql.connector.connect(
        host="localhost",  # 本機伺服器
        user="root",  # 你的 MySQL 帳號（預設通常是 root）
        password="8009026363",  # 💡 請換成你安裝 MySQL 時設定的密碼
        database="test_db"  # 指定連接你剛建的資料庫
    )

    if connection.is_connected():
        cursor = connection.cursor()

        # 2. 準備 SQL 寫入指令
        sql_query = """
        INSERT INTO stock_prices (stock_id, trade_date, open_price, close_price)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            open_price = VALUES(open_price), 
            close_price = VALUES(close_price);
        """

        # 3. 要寫入的資料內容 (符合你剛建的欄位：stock_id, trade_date, open_price, close_price)
        data_to_insert = ('2330', '2026-06-02', 910.00, 915.00)

        # 4. 執行 SQL 指令
        cursor.execute(sql_query, data_to_insert)

        # 5. 💡 非常重要：必須 commit 變更，資料才會真正寫入資料庫
        connection.commit()
        print(f"成功寫入 {cursor.rowcount} 筆股票資料！")

except mysql.connector.Error as error:
    print(f"連線或執行失敗: {error}")

finally:
    # 6. 關閉連線與游標
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()
        print("MySQL 連線已關閉。")