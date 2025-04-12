import os
import pandas as pd
import tkinter as tk
from tkinter import messagebox
from src.data_acquisition import DataAcquisition
from src.data_storage import DataStorage
from src.stock_screener import StockScreener

class StockSystemGUI:
    def __init__(self, config):
        self.data_acquisition = DataAcquisition(config.get_api_config()['tushare_token'])
        self.data_storage = DataStorage(config.get_database_config()['daily_db'])
        self.screener = StockScreener(config.get_database_config()['daily_db'])
        self._create_gui()

    def _create_gui(self):
        """Create the GUI interface."""
        self.root = tk.Tk()
        self.root.title("Stock System v1.0")
        self.root.geometry("400x400")
        self.root.resizable(False, False)

        tk.Button(
            self.root, text="Update Daily Data", command=self._update_daily,
            width=20, bg="lightgray", fg="black"
        ).pack(pady=10)
        tk.Button(
            self.root, text="获取全市场公司基础资料", command=self._update_basic_info,
            width=20, bg="lightgray", fg="black"
        ).pack(pady=10)
        tk.Button(
            self.root, text="Screen Stocks", command=self._screen_stocks,
            width=20, bg="lightblue", fg="black"
        ).pack(pady=10)
        tk.Button(
            self.root, text="Exit", command=self._exit, width=20, bg="lightgray", fg="black"
        ).pack(pady=10)

    def _update_daily(self):
        """Update daily data."""
        try:
            from datetime import datetime, timedelta
            import time

            latest_date = self.data_storage.get_latest_trade_date()
            start_date = (datetime.today() - timedelta(days=400)).strftime('%Y%m%d') if not latest_date else latest_date
            end_date = datetime.today().strftime('%Y%m%d')

            trade_cal = self.data_acquisition.get_trade_calendar(start_date, end_date)
            if trade_cal is None:
                messagebox.showerror("Error", "Failed to fetch trade calendar.")
                return

            start_date_dt = pd.to_datetime(start_date, format='%Y%m%d')
            end_date_dt = pd.to_datetime(end_date, format='%Y%m%d')
            new_dates = trade_cal[
                (trade_cal['cal_date'] >= start_date_dt) &
                (trade_cal['cal_date'] <= end_date_dt) &
                (trade_cal['is_open'] == 1)
            ]['cal_date'].dt.strftime('%Y%m%d').tolist()

            if not new_dates:
                messagebox.showinfo("Info", "No new daily data to update.")
                return

            total = len(new_dates)
            for idx, trade_date in enumerate(new_dates, 1):
                df = self.data_acquisition.get_daily_data(trade_date)
                if df is not None:
                    df = self.data_storage.clean_data(df)
                    self.data_storage.store_daily_data(df)
                print(f"Progress: {idx}/{total} [{trade_date}]", end='\r')
                time.sleep(1 if idx % 5 != 0 else 2)

            messagebox.showinfo("Success", "Daily data updated successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update daily data: {str(e)}")

    def _screen_stocks(self):
        """Run stock screening."""
        try:
            result = self.screener.run_screening()
            if result:
                messagebox.showinfo(
                    "Success",
                    f"Screening completed! Found {result['count']} stocks.\nSaved to: {result['path']}"
                )
            else:
                messagebox.showinfo("Info", "No stocks meet the criteria.")
        except Exception as e:
            messagebox.showerror("Error", f"Screening failed: {str(e)}")

    def _exit(self):
        """Exit the application."""
       # if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
        self.root.quit()

    def run(self):
        """Run the GUI main loop."""
        self.root.mainloop()

    def _update_basic_info(self):
        """获取全市场公司基础资料"""
        try:
            df = self.data_acquisition.get_stock_basic()
            if df is not None:
                save_path = os.path.join('data', 'stock_basic_all.csv')
                if self.data_storage.save_to_csv(df, save_path):
                    messagebox.showinfo("成功", f"已保存{len(df)}条上市公司数据到{save_path}")
                else:
                    messagebox.showerror("错误", "文件保存失败")
            else:
                messagebox.showerror("错误", "获取上市公司数据失败")
        except Exception as e:
            messagebox.showerror("错误", f"操作失败: {str(e)}")