import os
import sqlite3
import pandas as pd
from datetime import datetime
from tkinter import filedialog
import logging
import numpy as np
from src.technical_analyzer import TechnicalAnalyzer

class StockScreener:
    def __init__(self, daily_db_path):
        self.daily_db = daily_db_path
        self.analyzer = TechnicalAnalyzer()
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging."""
        logging.basicConfig(
            filename='data/logs/screening.log',
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def run_screening(self):
        """Run stock screening process."""
        try:
            # Select watchlist file
            csv_path = filedialog.askopenfilename(
                title="Select Watchlist CSV",
                filetypes=[("CSV files", "*.csv")]
            )
            if not csv_path:
                return None
            
            # Read stock codes
            watchlist = pd.read_csv(csv_path)
            ts_codes = watchlist['ts_code'].dropna().unique()
            
            # Connect to database
            conn = sqlite3.connect(self.daily_db)
            results = []
            
            # Screen each stock
            for ts_code in ts_codes:
                try:
                    df = pd.read_sql(
                        f"SELECT * FROM daily_data WHERE ts_code='{ts_code}' ORDER BY trade_date",
                        conn
                    )
                    if len(df) < 242:
                        continue
                    
                    df = self.analyzer.calculate_indicators(df)
                    if self.analyzer.check_conditions(df):
                        latest = df.iloc[-1]
                        results.append({
                            'ts_code': ts_code,
                            'close': round(latest['close'], 2),
                            'MA20': round(latest['MA20'], 2),
                            'MA60': round(latest['MA60'], 2),
                            'MA240': round(latest['MA240'], 2),
                            'RSI6': round(latest['RSI6'], 2),
                            'RSI13': round(latest['RSI13'], 2),
                            'VOL_MA3': round(latest['VOL_MA3'], 2),
                            'VOL_MA18': round(latest['VOL_MA18'], 2)
                        })
                except Exception as e:
                    logging.error(f"Failed to process stock {ts_code}: {str(e)}")
                    continue
            
            conn.close()
            
            # Save results
            if results:
                result_df = pd.DataFrame(results)
                numeric_cols = result_df.select_dtypes(include=[np.number]).columns
                result_df[numeric_cols] = result_df[numeric_cols].round(2)
                
                save_dir = "data/results"
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                # 合并基础信息
                basic_path = os.path.join('data', 'stock_basic_all.csv')
                try:
                    basic_df = pd.read_csv(basic_path, encoding='utf-8-sig')
                    merged_df = pd.merge(result_df,basic_df,on='ts_code')
                    merged_df.fillna('未知', inplace=True)
                    merged_df.to_csv(save_path, index=False, encoding='utf-8-sig', float_format='%.2f')
                except Exception as e:
                    logging.error(f"基础信息合并失败: {str(e)}")
                    result_df.to_csv(save_path, index=False, encoding='utf-8-sig', float_format='%.2f')
                return {'count': len(result_df), 'path': save_path}
            return None
        except Exception as e:
            logging.error(f"Screening process failed: {str(e)}")
            raise