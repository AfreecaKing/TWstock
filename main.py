import tkinter as tk
import download_data as download
import database as db
from tkinter import messagebox
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# 設定 matplotlib 支援中文
matplotlib.rcParams['font.family'] = ['Microsoft JhengHei', 'Microsoft YaHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


class TaiwanStockApp:
    def __init__(self, root):
        self.root = root
        self.root.title('台股管理系統')
        self.root.geometry("800x500")

        self.frame_stack = []
        self.current_frame = None

        # 加這一行，關閉視窗時確保程式完全結束
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        db.create_table()
        self.show_main_page()

    def _on_close(self):
        plt.close('all')  # 關閉所有 matplotlib 圖表
        self.root.destroy()  # 關閉 tkinter 視窗

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
        tk.Button(center_frame, text="分類漲跌比較", width=20, height=2, bg="lightgreen",
                  command=self.show_category_comparison_page).pack(pady=10)
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

            if ticker_code.endswith(('.TW', '.TWO')):
                final_ticker = ticker_code
                if download.insert_ticker(final_ticker):
                    for cat_id, var in category_vars.items():
                        if var.get():
                            db.assign_ticker_to_category(final_ticker, cat_id)
                    label_result.config(text=f"{final_ticker} 已新增完成！", fg="green")
                    entry.delete(0, tk.END)
                else:
                    label_result.config(text=f"新增失敗，請確認股票代號是否正確", fg="red")
            else:
                final_ticker = ticker_code + '.TW'
                label_result.config(text=f"嘗試 {final_ticker}...", fg="blue")
                self.root.update()

                if download.insert_ticker(final_ticker, silent=True):
                    print(f"✅ {final_ticker} 新增成功（上市股票）")
                    for cat_id, var in category_vars.items():
                        if var.get():
                            db.assign_ticker_to_category(final_ticker, cat_id)
                    label_result.config(text=f"{final_ticker} 已新增完成！", fg="green")
                    entry.delete(0, tk.END)
                else:
                    final_ticker = ticker_code + '.TWO'
                    label_result.config(text=f"嘗試 {final_ticker}...", fg="blue")
                    self.root.update()

                    if download.insert_ticker(final_ticker):
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

        tk.Button(btn_frame, text="📊 全部股票", width=30, height=2, font=("Arial", 11),
                  command=lambda: self.show_all_ticker_page(None, "全部股票")).pack(pady=5)

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

        tk.Label(name_frame, text=f"股票清單 - {category_name}", font=("Arial", 16)).pack(pady=5)

        # 分類5日綜合平均漲跌幅
        avg = db.get_category_avg_change_5d(category_id)
        if avg is not None:
            avg_text = f"分類5日綜合平均漲跌幅：{avg:+.2f}%"
            avg_color = "red" if avg > 0 else "green" if avg < 0 else "gray"
            tk.Label(name_frame, text=avg_text, font=("Arial", 12, "bold"), fg=avg_color).pack(pady=5)
        else:
            tk.Label(name_frame, text="分類5日綜合平均漲跌幅：無資料", font=("Arial", 12), fg="gray").pack(pady=5)

        if category_id is None:
            tickers = db.get_all_tickers()
        else:
            tickers = [t[0] for t in db.get_tickers_by_category(category_id)]

        container = tk.Frame(name_frame)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        canvas = tk.Canvas(container)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for ticker in tickers:
            ticker_name = ticker[0] if isinstance(ticker, (tuple, list)) else ticker

            row = tk.Frame(scrollable_frame, relief=tk.RIDGE, borderwidth=1)
            row.pack(fill=tk.X, pady=3, padx=5)

            ticker_cats = db.get_ticker_categories(ticker_name)
            cat_labels = ", ".join([c[1] for c in ticker_cats]) if ticker_cats else "未分類"

            info_frame = tk.Frame(row)
            info_frame.pack(side=tk.LEFT, padx=10, pady=5)

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

    # ===== 分類漲跌比較圖頁面 =====
    def show_category_comparison_page(self):
        comp_frame = tk.Frame(self.root)

        tk.Label(comp_frame, text="各分類漲跌幅比較", font=("Arial", 16, "bold")).pack(pady=5)

        # 天數選擇列
        ctrl_frame = tk.Frame(comp_frame)
        ctrl_frame.pack(pady=5)

        tk.Label(ctrl_frame, text="統計天數：", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)

        self._comp_days = tk.IntVar(value=5)

        for label, days in [("5日", 5), ("10日", 10), ("20日", 20), ("60日", 60)]:
            tk.Radiobutton(
                ctrl_frame, text=label, variable=self._comp_days,
                value=days, font=("Arial", 10),
                command=lambda: self._redraw_comparison(fig, ax, canvas_widget)
            ).pack(side=tk.LEFT, padx=4)

        # 圖表區域
        fig, ax = plt.subplots(figsize=(7, 4))
        fig.patch.set_facecolor('#F8F8F8')

        canvas_widget = FigureCanvasTkAgg(fig, comp_frame)
        canvas_widget.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tk.Button(comp_frame, text="返回", width=15, command=self.back).pack(pady=8)

        self.show_frame(comp_frame)

        # 儲存供 redraw 用
        self._comp_fig = fig
        self._comp_ax = ax
        self._comp_canvas = canvas_widget

        self._redraw_comparison(fig, ax, canvas_widget)

    def _redraw_comparison(self, fig, ax, canvas_widget):
        """重新繪製分類比較圖"""
        days = self._comp_days.get()
        data = db.get_all_categories_avg_change(days=days)

        ax.clear()
        fig.patch.set_facecolor('#F8F8F8')
        ax.set_facecolor('#F8F8F8')

        if not data:
            ax.text(0.5, 0.5, "目前沒有可比較的分類資料",
                    ha='center', va='center', fontsize=13, color='gray',
                    transform=ax.transAxes)
            canvas_widget.draw()
            return

        names = [d['name'] for d in data]
        changes = [d['avg_change'] for d in data]
        counts = [d['ticker_count'] for d in data]

        # 依漲跌決定顏色
        colors = ['#E8534A' if c > 0 else '#3DAA6E' if c < 0 else '#AAAAAA' for c in changes]

        # 水平長條圖（由上到下為高到低）
        y_pos = range(len(names))
        bars = ax.barh(y_pos, changes, color=colors, height=0.6, edgecolor='white', linewidth=0.8)

        # Y 軸標籤
        ax.set_yticks(list(y_pos))
        ax.set_yticklabels(names, fontsize=10)

        # 每條 bar 右側標示數值與股票數
        for i, (bar, change, count) in enumerate(zip(bars, changes, counts)):
            x_val = bar.get_width()
            offset = max(abs(x) for x in changes) * 0.03 if changes else 0.05
            ha = 'left' if x_val >= 0 else 'right'
            x_pos = x_val + offset if x_val >= 0 else x_val - offset
            ax.text(x_pos, bar.get_y() + bar.get_height() / 2,
                    f"{change:+.2f}%  ({count}檔)",
                    va='center', ha=ha, fontsize=9,
                    color='#333333')

        # 零軸線
        ax.axvline(x=0, color='#888888', linewidth=1.0, linestyle='--')

        ax.set_xlabel("平均漲跌幅 (%)", fontsize=10)
        ax.set_title(f"各分類 {days} 日平均漲跌幅比較（由高到低）", fontsize=12, pad=10)

        # 反轉 Y 軸讓最高的在上面
        ax.invert_yaxis()

        # 移除多餘邊框
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#CCCCCC')
        ax.spines['bottom'].set_color('#CCCCCC')

        ax.grid(axis='x', alpha=0.3, linestyle='--')
        fig.tight_layout()
        canvas_widget.draw()

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
            for cat_id, _ in categories:
                db.remove_ticker_from_category(ticker, cat_id)
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

        tk.Label(mgmt_frame, text="現有分類：", font=("Arial", 12)).pack(pady=10)

        cat_list_frame = tk.Frame(mgmt_frame)
        cat_list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.refresh_category_list(cat_list_frame)

        tk.Button(mgmt_frame, text="返回", width=15, command=self.back).pack(pady=10)

        self.show_frame(mgmt_frame)

    def refresh_category_list(self, parent_frame):
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
        market_frame = tk.Frame(self.root)

        tk.Label(market_frame, text="台股加權指數 (^TWII)", font=("Arial", 16)).pack(pady=10)

        loading_label = tk.Label(market_frame, text="正在載入大盤資料...", font=("Arial", 12), fg="blue")
        loading_label.pack(pady=20)

        self.show_frame(market_frame)
        self.root.update()

        import yfinance as yf
        try:
            ticker_obj = yf.Ticker("^TWII")
            df = ticker_obj.history(period="max")

            if df.empty:
                loading_label.config(text="無法取得大盤資料", fg="red")
                tk.Button(market_frame, text="返回", command=self.back).pack(pady=10)
                return

            df = df.reset_index()
            df = df.rename(columns={
                'Date': 'date', 'Close': 'close', 'Volume': 'volume',
                'Open': 'open', 'High': 'high', 'Low': 'low'
            })
            df['date'] = pd.to_datetime(df['date'])

            loading_label.destroy()

            self.ticker = "^TWII"
            self.df = df
            self.time_offset = 0
            self.current_period = "6M"
            self.chart_type = "price"
            self.ma_periods = [20, 40, 60]

            ma_frame = tk.Frame(market_frame)
            ma_frame.pack(pady=5)
            tk.Label(ma_frame, text="均線天數（以逗號分隔）：", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
            self.ma_entry = tk.Entry(ma_frame, width=20, font=("Arial", 10))
            self.ma_entry.insert(0, "20,40,60")
            self.ma_entry.pack(side=tk.LEFT, padx=5)
            tk.Button(ma_frame, text="更新", command=self.update_ma_periods).pack(side=tk.LEFT, padx=5)

            control_frame = tk.Frame(market_frame)
            control_frame.pack(pady=5)
            tk.Button(control_frame, text="指數走勢", command=lambda: self.set_chart_type("price")).pack(side=tk.LEFT,
                                                                                                         padx=5)
            tk.Button(control_frame, text="漲跌幅", command=lambda: self.set_chart_type("change")).pack(side=tk.LEFT,
                                                                                                        padx=5)
            tk.Button(control_frame, text="成交量", command=lambda: self.set_chart_type("volume")).pack(side=tk.LEFT,
                                                                                                        padx=5)
            tk.Button(control_frame, text="MACD", command=lambda: self.set_chart_type("macd")).pack(side=tk.LEFT,
                                                                                                    padx=5)

            period_frame = tk.Frame(market_frame)
            period_frame.pack(pady=5)
            tk.Button(period_frame, text="1個月", command=lambda: self.set_period("1M")).pack(side=tk.LEFT, padx=3)
            tk.Button(period_frame, text="3個月", command=lambda: self.set_period("3M")).pack(side=tk.LEFT, padx=3)
            tk.Button(period_frame, text="6個月", command=lambda: self.set_period("6M")).pack(side=tk.LEFT, padx=3)
            tk.Button(period_frame, text="1年", command=lambda: self.set_period("1Y")).pack(side=tk.LEFT, padx=3)
            tk.Button(period_frame, text="全部", command=lambda: self.set_period("ALL")).pack(side=tk.LEFT, padx=3)

            nav_frame = tk.Frame(market_frame)
            nav_frame.pack(pady=5)
            tk.Button(nav_frame, text="◀ 上一段", command=self.prev_period).pack(side=tk.LEFT, padx=5)
            tk.Button(nav_frame, text="下一段 ▶", command=self.next_period).pack(side=tk.LEFT, padx=5)

            self.figure = plt.Figure(figsize=(7, 4))
            self.ax = self.figure.add_subplot(111)
            self.canvas = FigureCanvasTkAgg(self.figure, market_frame)
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            tk.Button(market_frame, text="返回", command=self.back).pack(pady=5)

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
        self.ma_periods = [20, 40, 60]

        chart_frame = tk.Frame(self.root)

        display_name = ticker.replace('.TW', '').replace('.TWO', '')
        tk.Label(chart_frame, text=f"{display_name} 技術分析", font=("Arial", 16)).pack(pady=5)

        ma_frame = tk.Frame(chart_frame)
        ma_frame.pack(pady=5)
        tk.Label(ma_frame, text="均線天數（以逗號分隔）：", font=("Arial", 10)).pack(side=tk.LEFT, padx=5)
        self.ma_entry = tk.Entry(ma_frame, width=20, font=("Arial", 10))
        self.ma_entry.insert(0, "20,40,60")
        self.ma_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(ma_frame, text="更新", command=self.update_ma_periods).pack(side=tk.LEFT, padx=5)

        control_frame = tk.Frame(chart_frame)
        control_frame.pack(pady=5)
        tk.Button(control_frame, text="股價走勢", command=lambda: self.set_chart_type("price")).pack(side=tk.LEFT,
                                                                                                     padx=5)
        tk.Button(control_frame, text="漲跌幅", command=lambda: self.set_chart_type("change")).pack(side=tk.LEFT,
                                                                                                    padx=5)
        tk.Button(control_frame, text="成交量", command=lambda: self.set_chart_type("volume")).pack(side=tk.LEFT,
                                                                                                    padx=5)
        tk.Button(control_frame, text="MACD", command=lambda: self.set_chart_type("macd")).pack(side=tk.LEFT, padx=5)

        period_frame = tk.Frame(chart_frame)
        period_frame.pack(pady=5)
        tk.Button(period_frame, text="1個月", command=lambda: self.set_period("1M")).pack(side=tk.LEFT, padx=3)
        tk.Button(period_frame, text="3個月", command=lambda: self.set_period("3M")).pack(side=tk.LEFT, padx=3)
        tk.Button(period_frame, text="6個月", command=lambda: self.set_period("6M")).pack(side=tk.LEFT, padx=3)
        tk.Button(period_frame, text="1年", command=lambda: self.set_period("1Y")).pack(side=tk.LEFT, padx=3)
        tk.Button(period_frame, text="全部", command=lambda: self.set_period("ALL")).pack(side=tk.LEFT, padx=3)

        nav_frame = tk.Frame(chart_frame)
        nav_frame.pack(pady=5)
        tk.Button(nav_frame, text="◀ 上一段", command=self.prev_period).pack(side=tk.LEFT, padx=5)
        tk.Button(nav_frame, text="下一段 ▶", command=self.next_period).pack(side=tk.LEFT, padx=5)

        self.figure = plt.Figure(figsize=(7, 4))
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        tk.Button(chart_frame, text="返回", command=self.back).pack(pady=5)

        self.show_frame(chart_frame)
        self.draw_chart(self.chart_type, self.current_period)

    def update_ma_periods(self):
        try:
            input_str = self.ma_entry.get().strip()
            if not input_str:
                self.ma_periods = []
            else:
                self.ma_periods = [int(x.strip()) for x in input_str.split(',')]
                if any(p <= 0 for p in self.ma_periods):
                    messagebox.showwarning("警告", "均線天數必須為正整數")
                    self.ma_entry.delete(0, tk.END)
                    self.ma_entry.insert(0, "20,40,60")
                    return
            self.draw_chart(self.chart_type, self.current_period)
        except ValueError:
            messagebox.showwarning("警告", "請輸入正確的數字，以逗號分隔（例如：20,40,60）")
            self.ma_entry.delete(0, tk.END)
            self.ma_entry.insert(0, "20,40,60")

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

        for ma_period in self.ma_periods:
            if len(df) >= ma_period:
                df[f'MA{ma_period}'] = df['close'].rolling(ma_period).mean()

        df['EMA12'] = df['close'].ewm(span=12).mean()
        df['EMA26'] = df['close'].ewm(span=26).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=9).mean()
        df['Histogram'] = df['MACD'] - df['Signal']

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

        if chart_type == "price":
            self.ax.plot(df["date"], df["close"], label="Close Price", color='blue', linewidth=1.5)
            colors = ['orange', 'red', 'green', 'purple', 'brown', 'pink']
            for idx, ma_period in enumerate(self.ma_periods):
                ma_col = f'MA{ma_period}'
                if ma_col in df.columns:
                    color = colors[idx % len(colors)]
                    self.ax.plot(df["date"], df[ma_col], label=f"MA{ma_period}", color=color, linewidth=1, alpha=0.7)
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
            avg_volume = df['volume'].mean()
            self.ax.axhline(y=avg_volume, color='blue', linestyle='--', linewidth=1.5,
                            label=f'Avg: {avg_volume:,.0f}')
            self.ax.legend(loc='best')
            self.ax.grid(True, alpha=0.3)

        elif chart_type == "macd":
            self.ax.plot(df["date"], df['MACD'], label='MACD', color='blue', linewidth=2)
            self.ax.plot(df["date"], df['Signal'], label='Signal', color='red', linewidth=2)
            colors = ['green' if x >= 0 else 'red' for x in df['Histogram']]
            self.ax.bar(df["date"], df['Histogram'], label='Histogram', color=colors, alpha=0.3, width=0.8)
            self.ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
            self.ax.set_title(f"{display_name} MACD ({period})", fontsize=12)
            self.ax.set_ylabel("MACD Value", fontsize=10)
            self.ax.legend(loc='best')
            self.ax.grid(True, alpha=0.3)

        self.ax.set_xlabel("Date", fontsize=10)
        self.figure.autofmt_xdate()
        self.canvas.draw()


if __name__ == "__main__":
    root = tk.Tk()
    app = TaiwanStockApp(root)
    root.mainloop()
