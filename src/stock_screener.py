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
        """运行股票筛选过程，输出所有股票及其筛选结果"""
        try:
            # 选择观察列表文件
            csv_path = filedialog.askopenfilename(
                title="选择观察列表 CSV",
                filetypes=[("CSV 文件", "*.csv")]
            )
            if not csv_path:
                return None
            
            # 读取股票代码
            watchlist = pd.read_csv(csv_path)
            ts_codes = watchlist['ts_code'].dropna().unique()
            
            # 连接数据库
            conn = sqlite3.connect(self.daily_db)
            results = []
            
            # 筛选每只股票
            for ts_code in ts_codes:
                try:
                    df = pd.read_sql(
                        f"SELECT * FROM daily_data WHERE ts_code='{ts_code}' ORDER BY trade_date",
                        conn
                    )
                    if len(df) < 242:
                        results.append({
                            'ts_code': ts_code,
                            'result': 99
                        })
                        continue
                    
                    df = self.analyzer.calculate_indicators(df)
                    result_df = self.analyzer.check_conditions(df)
                    result_code = result_df.iloc[0]['result']
                    
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
                        'VOL_MA18': round(latest['VOL_MA18'], 2),
                        'result': result_code
                    })
                except Exception as e:
                    logging.error(f"处理股票 {ts_code} 失败: {str(e)}")
                    results.append({
                        'ts_code': ts_code,
                        'result': -1  # 表示处理错误
                    })
                    continue
            
            conn.close()
            
            # 保存结果
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
                    merged_df = pd.merge(result_df, basic_df, on='ts_code', how='left')
                    merged_df.fillna('未知', inplace=True)
                    merged_df.to_csv(save_path, index=False, encoding='utf-8-sig', float_format='%.2f')
                except Exception as e:
                    logging.error(f"基础信息合并失败: {str(e)}")
                    result_df.to_csv(save_path, index=False, encoding='utf-8-sig', float_format='%.2f')
                return {'count': len(result_df), 'path': save_path}
            return None
        except Exception as e:
            logging.error(f"筛选过程失败: {str(e)}")
            raise