import tkinter as tk
import download_data as download
import database as db
from tkinter import messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class TaiwanStockApp:
    def __init__(self, root):
        self.root = root
        self.root.title('台股管理系統')
        self.root.geometry("800x500")

        self.frame_stack = []
        self.current_frame = None

        db.create_table()
        self.show_main_page()

    def show_frame(self, new_frame):
        if self.current_frame:
            self.frame_stack.append(self.current_frame)
            self.current_frame.pack_forget()
        new_frame.pack(fill=tk.BOTH, expand=True)
        self.current_frame = new_frame

    def replace_frame(self, new_frame):
        if self.current_frame:
            self.current_frame.pack_forget()
        new_frame.pack(fill=tk.BOTH, expand=True)
        self.current_frame = new_frame

    def back(self):
        if not self.frame_stack:
            self.show_main_page()
            return
        if self.current_frame:
            self.current_frame.pack_forget()
            self.current_frame.destroy()
        self.current_frame = self.frame_stack.pop()
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    # ===== 主頁面 =====
    def show_main_page(self):
        for frame in self.frame_stack:
            frame.destroy()
        self.frame_stack.clear()

        if self.current_frame:
            self.current_frame.pack_forget()
            self.current_frame.destroy()

        main_frame = tk.Frame(self.root)
        center_frame = tk.Frame(main_frame)
        center_frame.pack(expand=True)

        tk.Label(center_frame, text="台股管理系統", font=("Arial", 20, "bold")).pack(pady=20)

        tk.Button(center_frame, text="查看大盤", width=20, height=2, bg="lightyellow",
                  command=self.show_market_index).pack(pady=10)
        tk.Button(center_frame, text="新增股票", width=20, height=2,
                  command=self.show_insert_page).pack(pady=10)
        tk.Button(center_frame, text="瀏覽股票", width=20, height=2,
                  command=self.show_category_selection_page).pack(pady=10)
        tk.Button(center_frame, text="管理分類", width=20, height=2,
                  command=self.show_category_management_page).pack(pady=10)
        tk.Button(center_frame, text="更新所有股價", width=20, height=2, bg="lightblue",
                  command=download.update_all_ticker).pack(pady=10)

        main_frame.pack(fill=tk.BOTH, expand=True)
        self.current_frame = main_frame

    # ===== 新增股票頁面 =====
    def show_insert_page(self):
        insert_frame = tk.Frame(self.root)

        tk.Label(insert_frame, text="輸入股票代號（例如：2330）", font=("Arial", 12)).pack(pady=10)
        entry = tk.Entry(insert_frame, font=("Arial", 12), width=15)
        entry.pack(pady=5)

        tk.Label(insert_frame, text="選擇分類（可多選）", font=("Arial", 11)).pack(pady=10)

        # 分類選擇區
        categories = db.get_all_categories()
        category_vars = {}

        cat_container = tk.Frame(insert_frame)
        cat_container.pack(pady=5, fill=tk.BOTH, expand=True)

        cat_canvas = tk.Canvas(cat_container, height=150)
        cat_scrollbar = tk.Scrollbar(cat_container, orient="vertical", command=cat_canvas.yview)
        cat_frame = tk.Frame(cat_canvas)

        cat_frame.bind("<Configure>", lambda e: cat_canvas.configure(scrollregion=cat_canvas.bbox("all")))
        cat_canvas.create_window((0, 0), window=cat_frame, anchor="nw")
        cat_canvas.configure(yscrollcommand=cat_scrollbar.set)

        for cat_id, cat_name in categories:
            var = tk.BooleanVar()
            category_vars[cat_id] = var
            tk.Checkbutton(cat_frame, text=cat_name, variable=var, font=("Arial", 10)).pack(anchor=tk.W, padx=20)

        cat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        label_result = tk.Label(insert_frame, text="", font=("Arial", 10))
        label_result.pack(pady=10)

        def insert_stock():
            ticker_code = entry.get().strip()
            if not ticker_code:
                label_result.config(text="請輸入股票代號", fg="red")
                return

            # 如果已經有後綴，直接使用
            if ticker_code.endswith(('.TW', '.TWO')):
                final_ticker = ticker_code
                if download.insert_ticker(final_ticker):
                    # 成功新增後指定分類
                    for cat_id, var in category_vars.items():
                        if var.get():
                            db.assign_ticker_to_category(final_ticker, cat_id)
                    label_result.config(text=f"{final_ticker} 已新增完成！", fg="green")
                    entry.delete(0, tk.END)
                else:
                    label_result.config(text=f"新增失敗，請確認股票代號是否正確", fg="red")
            else:
                # 先嘗試 .TW（上市）- 靜默模式
                final_ticker = ticker_code + '.TW'
                label_result.config(text=f"嘗試 {final_ticker}...", fg="blue")
                self.root.update()

                if download.insert_ticker(final_ticker, silent=True):
                    # .TW 成功
                    print(f"✅ {final_ticker} 新增成功（上市股票）")
                    for cat_id, var in category_vars.items():
                        if var.get():
                            db.assign_ticker_to_category(final_ticker, cat_id)
                    label_result.config(text=f"{final_ticker} 已新增完成！", fg="green")
                    entry.delete(0, tk.END)
                else:
                    # .TW 失敗，嘗試 .TWO（上櫃）
                    final_ticker = ticker_code + '.TWO'
                    label_result.config(text=f"嘗試 {final_ticker}...", fg="blue")
                    self.root.update()

                    if download.insert_ticker(final_ticker):
                        # .TWO 成功
                        print(f"✅ {final_ticker} 新增成功（上櫃股票）")
                        for cat_id, var in category_vars.items():
                            if var.get():
                                db.assign_ticker_to_category(final_ticker, cat_id)
                        label_result.config(text=f"{final_ticker} 已新增完成！", fg="green")
                        entry.delete(0, tk.END)
                    else:
                        label_result.config(text=f"新增失敗，請確認股票代號 {ticker_code} 是否正確", fg="red")

        tk.Button(insert_frame, text="新增", width=15, command=insert_stock).pack(pady=5)
        tk.Button(insert_frame, text="返回", width=15, command=self.back).pack(pady=5)

        self.show_frame(insert_frame)

    # ===== 分類選擇頁面 =====
    def show_category_selection_page(self):
        cat_sel_frame = tk.Frame(self.root)

        tk.Label(cat_sel_frame, text="選擇分類", font=("Arial", 16)).pack(pady=10)

        categories = db.get_all_categories()

        container = tk.Frame(cat_sel_frame)
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        btn_frame = tk.Frame(canvas)

        btn_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=btn_frame, anchor="n")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 全部股票按鈕
        tk.Button(btn_frame, text="📊 全部股票", width=30, height=2, font=("Arial", 11),
                  command=lambda: self.show_all_ticker_page(None, "全部股票")).pack(pady=5)

        # 各分類按鈕
        for cat_id, cat_name in categories:
            tk.Button(btn_frame, text=f"📁 {cat_name}", width=30, height=2, font=("Arial", 11),
                      command=lambda cid=cat_id, cn=cat_name: self.show_all_ticker_page(cid, cn)).pack(pady=5)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Button(cat_sel_frame, text="返回", width=15, command=self.back).pack(pady=10)

        self.show_frame(cat_sel_frame)

    # ===== 股票清單頁面 =====
    def show_all_ticker_page(self, category_id=None, category_name="全部股票"):
        name_frame = tk.Frame(self.root)

        tk.Label(name_frame, text=f"股票清單 - {category_name}", font=("Arial", 16)).pack(pady=10)

        # 取得股票列表
        if category_id is None:
            tickers = db.get_all_tickers()
        else:
            tickers = [t[0] for t in db.get_tickers_by_category(category_id)]

        # 建立可滾動的 Frame
        container = tk.Frame(name_frame)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # 股票列表
        for ticker in tickers:
            ticker_name = ticker[0] if isinstance(ticker, (tuple, list)) else ticker

            row = tk.Frame(scrollable_frame, relief=tk.RIDGE, borderwidth=1)
            row.pack(fill=tk.X, pady=3, padx=5)

            # 顯示股票分類標籤
            ticker_cats = db.get_ticker_categories(ticker_name)
            cat_labels = ", ".join([c[1] for c in ticker_cats]) if ticker_cats else "未分類"

            info_frame = tk.Frame(row)
            info_frame.pack(side=tk.LEFT, padx=10, pady=5)

            # 顯示股票代號（移除 .TW 後綴以便閱讀）
            display_name = ticker_name.replace('.TW', '').replace('.TWO', '')
            tk.Label(info_frame, text=display_name, font=("Arial", 12, "bold")).pack(anchor=tk.W)
            tk.Label(info_frame, text=f"[{cat_labels}]", font=("Arial", 9), fg="gray").pack(anchor=tk.W)

            tk.Button(row, text="技術分析", width=12,
                      command=lambda t=ticker_name: self.view_ticker(t)).pack(side=tk.LEFT, padx=5)
            tk.Button(row, text="編輯分類", width=10,
                      command=lambda t=ticker_name: self.edit_ticker_categories(t)).pack(side=tk.LEFT, padx=5)
            tk.Button(row, text="刪除", width=8, fg="white", bg="red",
                      command=lambda t=ticker_name: self.delete_ticker_ui(t, category_id, category_name)).pack(
                side=tk.LEFT, padx=5)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tk.Button(name_frame, text="返回", width=15, command=self.back).pack(pady=10)

        self.show_frame(name_frame)

    # ===== 編輯股票分類 =====
    def edit_ticker_categories(self, ticker):
        edit_frame = tk.Frame(self.root)

        display_name = ticker.replace('.TW', '').replace('.TWO', '')
        tk.Label(edit_frame, text=f"編輯 {display_name} 的分類", font=("Arial", 14)).pack(pady=10)

        categories = db.get_all_categories()
        current_cats = [c[0] for c in db.get_ticker_categories(ticker)]

        category_vars = {}

        cat_container = tk.Frame(edit_frame)
        cat_container.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)

        cat_canvas = tk.Canvas(cat_container, height=200)
        cat_scrollbar = tk.Scrollbar(cat_container, orient="vertical", command=cat_canvas.yview)
        cat_frame = tk.Frame(cat_canvas)

        cat_frame.bind("<Configure>", lambda e: cat_canvas.configure(scrollregion=cat_canvas.bbox("all")))
        cat_canvas.create_window((0, 0), window=cat_frame, anchor="nw")
        cat_canvas.configure(yscrollcommand=cat_scrollbar.set)

        for cat_id, cat_name in categories:
            var = tk.BooleanVar(value=(cat_id in current_cats))
            category_vars[cat_id] = var
            tk.Checkbutton(cat_frame, text=cat_name, variable=var, font=("Arial", 10)).pack(anchor=tk.W, padx=20)

        cat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cat_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def save_categories():
            # 先移除所有分類
            for cat_id, _ in categories:
                db.remove_ticker_from_category(ticker, cat_id)

            # 重新指定選中的分類
            for cat_id, var in category_vars.items():
                if var.get():
                    db.assign_ticker_to_category(ticker, cat_id)

            messagebox.showinfo("成功", f"{display_name} 的分類已更新")
            self.back()

        tk.Button(edit_frame, text="儲存", width=15, command=save_categories).pack(pady=10)
        tk.Button(edit_frame, text="返回", width=15, command=self.back).pack(pady=5)

        self.show_frame(edit_frame)

    # ===== 分類管理頁面 =====
    def show_category_management_page(self):
        mgmt_frame = tk.Frame(self.root)

        tk.Label(mgmt_frame, text="分類管理", font=("Arial", 16)).pack(pady=10)

        # 新增分類
        add_frame = tk.Frame(mgmt_frame)
        add_frame.pack(pady=10)

        tk.Label(add_frame, text="新增分類：", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        new_cat_entry = tk.Entry(add_frame, width=20, font=("Arial", 11))
        new_cat_entry.pack(side=tk.LEFT, padx=5)

        def add_new_category():
            name = new_cat_entry.get().strip()
            if not name:
                messagebox.showwarning("警告", "請輸入分類名稱")
                return
            if db.add_category(name):
                messagebox.showinfo("成功", f"已新增分類：{name}")
                new_cat_entry.delete(0, tk.END)
                self.refresh_category_list(cat_list_frame)
            else:
                messagebox.showerror("失敗", "分類已存在或新增失敗")

        tk.Button(add_frame, text="新增", command=add_new_category).pack(side=tk.LEFT, padx=5)

        # 現有分類列表
        tk.Label(mgmt_frame, text="現有分類：", font=("Arial", 12)).pack(pady=10)

        cat_list_frame = tk.Frame(mgmt_frame)
        cat_list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.refresh_category_list(cat_list_frame)

        tk.Button(mgmt_frame, text="返回", width=15, command=self.back).pack(pady=10)

        self.show_frame(mgmt_frame)

    def refresh_category_list(self, parent_frame):
        """刷新分類列表"""
        for widget in parent_frame.winfo_children():
            widget.destroy()

        categories = db.get_all_categories()

        for cat_id, cat_name in categories:
            row = tk.Frame(parent_frame, relief=tk.RIDGE, borderwidth=1)
            row.pack(fill=tk.X, pady=2)

            tk.Label(row, text=cat_name, width=20, anchor=tk.W, font=("Arial", 10)).pack(side=tk.LEFT, padx=10)
            tk.Button(row, text="刪除", width=8, bg="lightcoral",
                      command=lambda cid=cat_id, cn=cat_name: self.delete_category_ui(cid, cn, parent_frame)).pack(
                side=tk.LEFT, padx=5)

    def delete_category_ui(self, category_id, category_name, parent_frame):
        """刪除分類"""
        if not messagebox.askyesno("確認", f"確定要刪除分類「{category_name}」嗎？\n（股票不會被刪除，只會解除分類關聯）"):
            return

        if db.delete_category(category_id):
            messagebox.showinfo("成功", f"已刪除分類：{category_name}")
            self.refresh_category_list(parent_frame)
        else:
            messagebox.showerror("失敗", "刪除分類失敗")

    # ===== 刪除股票 =====
    def delete_ticker_ui(self, ticker, category_id=None, category_name="全部股票"):
        display_name = ticker.replace('.TW', '').replace('.TWO', '')
        if not messagebox.askyesno("確認刪除", f"確定要刪除 {display_name} 的所有資料嗎？"):
            return

        if db.delete_ticker(ticker):
            messagebox.showinfo("成功", f"{display_name} 已刪除")
            if self.current_frame:
                self.current_frame.pack_forget()
                self.current_frame.destroy()
            self.show_all_ticker_page(category_id, category_name)
        else:
            messagebox.showerror("失敗", f"{display_name} 刪除失敗")

    # ===== 查看大盤 =====
    def show_market_index(self):
        """顯示台股大盤走勢"""
        market_frame = tk.Frame(self.root)

        tk.Label(market_frame, text="台股加權指數 (^TWII)", font=("Arial", 16)).pack(pady=10)

        # 顯示載入訊息
        loading_label = tk.Label(market_frame, text="正在載入大盤資料...", font=("Arial", 12), fg="blue")
        loading_label.pack(pady=20)

        self.show_frame(market_frame)
        self.root.update()

        # 下載大盤資料
        import yfinance as yf
        try:
            ticker_obj = yf.Ticker("^TWII")
            df = ticker_obj.history(period="max")

            if df.empty:
                loading_label.config(text="無法取得大盤資料", fg="red")
                tk.Button(market_frame, text="返回", command=self.back).pack(pady=10)
                return

            # 處理資料格式
            df = df.reset_index()
            df = df.rename(columns={
                'Date': 'date',
                'Close': 'close',
                'Volume': 'volume',
                'Open': 'open',
                'High': 'high',
                'Low': 'low'
            })
            df['date'] = pd.to_datetime(df['date'])

            # 移除載入訊息
            loading_label.destroy()

            # 設定圖表參數
            self.ticker = "^TWII"
            self.df = df
            self.time_offset = 0
            self.current_period = "6M"
            self.chart_type = "price"

            # 圖表類型選擇
            control_frame = tk.Frame(market_frame)
            control_frame.pack(pady=5)
            tk.Button(control_frame, text="指數走勢", command=lambda: self.set_chart_type("price")).pack(side=tk.LEFT,
                                                                                                         padx=5)
            tk.Button(control_frame, text="漲跌幅", command=lambda: self.set_chart_type("change")).pack(side=tk.LEFT,
                                                                                                        padx=5)
            tk.Button(control_frame, text="成交量", command=lambda: self.set_chart_type("volume")).pack(side=tk.LEFT,
                                                                                                        padx=5)

            # 時間範圍選擇
            period_frame = tk.Frame(market_frame)
            period_frame.pack(pady=5)
            tk.Button(period_frame, text="1個月", command=lambda: self.set_period("1M")).pack(side=tk.LEFT, padx=3)
            tk.Button(period_frame, text="3個月", command=lambda: self.set_period("3M")).pack(side=tk.LEFT, padx=3)
            tk.Button(period_frame, text="6個月", command=lambda: self.set_period("6M")).pack(side=tk.LEFT, padx=3)
            tk.Button(period_frame, text="1年", command=lambda: self.set_period("1Y")).pack(side=tk.LEFT, padx=3)
            tk.Button(period_frame, text="全部", command=lambda: self.set_period("ALL")).pack(side=tk.LEFT, padx=3)

            # 時間軸導航
            nav_frame = tk.Frame(market_frame)
            nav_frame.pack(pady=5)
            tk.Button(nav_frame, text="◀ 上一段", command=self.prev_period).pack(side=tk.LEFT, padx=5)
            tk.Button(nav_frame, text="下一段 ▶", command=self.next_period).pack(side=tk.LEFT, padx=5)

            # 圖表區域
            self.figure = plt.Figure(figsize=(7, 4))
            self.ax = self.figure.add_subplot(111)
            self.canvas = FigureCanvasTkAgg(self.figure, market_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            tk.Button(market_frame, text="返回", command=self.back).pack(pady=5)

            # 繪製圖表
            self.draw_chart(self.chart_type, self.current_period)

        except Exception as e:
            loading_label.config(text=f"載入失敗：{e}", fg="red")
            tk.Button(market_frame, text="返回", command=self.back).pack(pady=10)

    # ===== 技術面分析 =====
    def view_ticker(self, ticker):
        self.ticker = ticker
        self.df = db.select_price(ticker)

        if self.df.empty:
            messagebox.showinfo("無資料", f"{ticker} 尚無價格資料")
            return

        self.time_offset = 0
        self.current_period = "6M"
        self.chart_type = "price"

        chart_frame = tk.Frame(self.root)

        display_name = ticker.replace('.TW', '').replace('.TWO', '')
        tk.Label(chart_frame, text=f"{display_name} 技術分析", font=("Arial", 16)).pack(pady=5)

        # 圖表類型選擇
        control_frame = tk.Frame(chart_frame)
        control_frame.pack(pady=5)
        tk.Button(control_frame, text="股價走勢", command=lambda: self.set_chart_type("price")).pack(side=tk.LEFT,
                                                                                                     padx=5)
        tk.Button(control_frame, text="漲跌幅", command=lambda: self.set_chart_type("change")).pack(side=tk.LEFT,
                                                                                                    padx=5)
        tk.Button(control_frame, text="成交量", command=lambda: self.set_chart_type("volume")).pack(side=tk.LEFT,
                                                                                                    padx=5)

        # 時間範圍選擇
        period_frame = tk.Frame(chart_frame)
        period_frame.pack(pady=5)
        tk.Button(period_frame, text="1個月", command=lambda: self.set_period("1M")).pack(side=tk.LEFT, padx=3)
        tk.Button(period_frame, text="3個月", command=lambda: self.set_period("3M")).pack(side=tk.LEFT, padx=3)
        tk.Button(period_frame, text="6個月", command=lambda: self.set_period("6M")).pack(side=tk.LEFT, padx=3)
        tk.Button(period_frame, text="1年", command=lambda: self.set_period("1Y")).pack(side=tk.LEFT, padx=3)
        tk.Button(period_frame, text="全部", command=lambda: self.set_period("ALL")).pack(side=tk.LEFT, padx=3)

        # 時間軸導航
        nav_frame = tk.Frame(chart_frame)
        nav_frame.pack(pady=5)
        tk.Button(nav_frame, text="◀ 上一段", command=self.prev_period).pack(side=tk.LEFT, padx=5)
        tk.Button(nav_frame, text="下一段 ▶", command=self.next_period).pack(side=tk.LEFT, padx=5)

        # 圖表區域
        self.figure = plt.Figure(figsize=(7, 4))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        tk.Button(chart_frame, text="返回", command=self.back).pack(pady=5)

        self.show_frame(chart_frame)
        self.draw_chart(self.chart_type, self.current_period)

    def set_chart_type(self, chart_type):
        self.chart_type = chart_type
        self.time_offset = 0
        self.draw_chart(chart_type, self.current_period)

    def set_period(self, period):
        self.current_period = period
        self.time_offset = 0
        self.draw_chart(self.chart_type, period)

    def prev_period(self):
        self.time_offset += 1
        self.draw_chart(self.chart_type, self.current_period)

    def next_period(self):
        if self.time_offset > 0:
            self.time_offset -= 1
        self.draw_chart(self.chart_type, self.current_period)

    def draw_chart(self, chart_type="price", period="6M"):
        self.ax.clear()
        df = self.df.copy()

        # 先用完整資料計算移動平均線
        if len(df) >= 20:
            df['MA20'] = df['close'].rolling(20).mean()
        if len(df) >= 40:
            df['MA40'] = df['close'].rolling(40).mean()
        if len(df) >= 60:
            df['MA60'] = df['close'].rolling(60).mean()

        # 再根據時間範圍篩選要顯示的資料
        if period != "ALL":
            end_date = df["date"].max()
            if period == "1M":
                end_date -= pd.DateOffset(months=self.time_offset)
                start_date = end_date - pd.DateOffset(months=1)
            elif period == "3M":
                end_date -= pd.DateOffset(months=3 * self.time_offset)
                start_date = end_date - pd.DateOffset(months=3)
            elif period == "6M":
                end_date -= pd.DateOffset(months=6 * self.time_offset)
                start_date = end_date - pd.DateOffset(months=6)
            elif period == "1Y":
                end_date -= pd.DateOffset(years=self.time_offset)
                start_date = end_date - pd.DateOffset(years=1)
            df = df[(df["date"] > start_date) & (df["date"] <= end_date)]

        display_name = self.ticker.replace('.TW', '').replace('.TWO', '').replace('^TWII', 'TWII')

        # 繪製不同類型的圖表
        if chart_type == "price":
            self.ax.plot(df["date"], df["close"], label="Close Price", color='blue', linewidth=1.5)

            # 只要均線欄位存在就顯示（即使部分資料是 NaN）
            if 'MA20' in df.columns:
                self.ax.plot(df["date"], df['MA20'], label="MA20", color='orange', linewidth=1, alpha=0.7)
            if 'MA40' in df.columns:
                self.ax.plot(df["date"], df['MA40'], label="MA40", color='red', linewidth=1, alpha=0.7)
            if 'MA60' in df.columns:
                self.ax.plot(df["date"], df['MA60'], label="MA60", color='green', linewidth=1, alpha=0.7)

            self.ax.set_title(f"{display_name} Price Chart ({period})", fontsize=12)
            self.ax.set_ylabel("Price (TWD)", fontsize=10)
            self.ax.legend(loc='best')
            self.ax.grid(True, alpha=0.3)

        elif chart_type == "change":
            df['daily_change'] = df['close'].pct_change() * 100
            colors = ['red' if x > 0 else 'green' if x < 0 else 'gray' for x in df['daily_change']]
            self.ax.bar(df["date"], df['daily_change'], color=colors, alpha=0.7, width=0.8)
            self.ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
            self.ax.set_title(f"{display_name} Daily Change ({period})", fontsize=12)
            self.ax.set_ylabel("Change (%)", fontsize=10)
            avg_change = df['daily_change'].mean()
            self.ax.text(0.02, 0.98, f"Avg: {avg_change:.2f}%",
                         transform=self.ax.transAxes, verticalalignment='top',
                         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            self.ax.grid(True, alpha=0.3)

        elif chart_type == "volume":
            colors = ['red' if df.iloc[i]['close'] >= df.iloc[i]['open'] else 'green'
                      for i in range(len(df))]
            self.ax.bar(df["date"], df['volume'], color=colors, alpha=0.6, width=0.8)
            self.ax.set_title(f"{display_name} Volume ({period})", fontsize=12)
            self.ax.set_ylabel("Volume (shares)", fontsize=10)

            # 計算平均成交量並畫水平線
            avg_volume = df['volume'].mean()
            self.ax.axhline(y=avg_volume, color='blue', linestyle='--', linewidth=1.5,
                            label=f'Avg: {avg_volume:,.0f}')
            self.ax.legend(loc='best')
            self.ax.grid(True, alpha=0.3)

        self.ax.set_xlabel("Date", fontsize=10)
        self.figure.autofmt_xdate()
        self.canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = TaiwanStockApp(root)
    root.mainloop()