import os
import sqlite3
import pandas as pd
import logging

class DataStorage:
    def __init__(self, daily_db_path):
        """Initialize database connection and setup."""
        self.daily_db = daily_db_path
        os.makedirs(os.path.dirname(self.daily_db), exist_ok=True)
        self._setup_logging()
        self._init_tables()

    def _setup_logging(self):
        """Configure logging."""
        logging.basicConfig(
            filename='data/logs/data_update.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def _init_tables(self):
        """Create database tables."""
        with sqlite3.connect(self.daily_db) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS daily_data (
                    ts_code TEXT,
                    trade_date TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    vol REAL,
                    pe_ttm REAL,
                    pb REAL,
                    total_mv REAL,
                    PRIMARY KEY (ts_code, trade_date)
                )''')

    def clean_data(self, df):
        """Clean daily data."""
        if df.empty:
            return df
        df = df.dropna(subset=['ts_code', 'trade_date'])
        df = df.fillna({'pe_ttm': 0, 'pb': 0})
        return df.drop_duplicates(subset=['ts_code', 'trade_date'], keep='last')

    def get_latest_trade_date(self):
        """Get the latest trade date in the database."""
        with sqlite3.connect(self.daily_db) as conn:
            try:
                result = conn.execute(
                    "SELECT MAX(trade_date) FROM daily_data"
                ).fetchone()[0]
                return result
            except Exception as e:
                logging.error(f"Failed to get latest trade date: {str(e)}")
                return None

    def store_daily_data(self, df):
        """Store daily data in the database."""
        try:
            with sqlite3.connect(self.daily_db) as conn:
                existing_data = pd.read_sql("SELECT ts_code, trade_date FROM daily_data", conn)
                df = df.merge(existing_data, on=['ts_code', 'trade_date'], how='left', indicator=True)
                df = df[df['_merge'] == 'left_only'].drop(columns=['_merge'])
                if not df.empty:
                    df.to_sql('daily_data', conn, if_exists='append', index=False)
                return True
        except Exception as e:
            logging.error(f"Failed to store daily data: {str(e)}")
            return False

    def save_to_csv(self, df, file_path):
        """保存数据到CSV文件"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            logging.error(f"CSV保存失败: {str(e)}")
            return False

    def _update_financial(self):
        """获取全市场公司基础资料"""
        try:
            df = self.data_acquisition.get_stock_basic()
            if df is not None:
                save_path = os.path.join('data', 'stock_basic_all.csv')
                if self.data_storage.save_to_csv(df, save_path):
                    messagebox.showinfo("成功", f"已保存{len(df)}条记录到{save_path}")
                else:
                    messagebox.showerror("错误", "文件保存失败")
            else:
                messagebox.showerror("错误", "获取上市公司数据失败")
        except Exception as e:
            messagebox.showerror("错误", f"操作失败: {str(e)}")