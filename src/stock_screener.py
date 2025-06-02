import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from tkinter import filedialog
import logging
from concurrent.futures import ProcessPoolExecutor
from src.technical_analyzer import TechnicalAnalyzer

def process_stock(ts_code, df, analyzer):
    """Process a single stock for parallel execution."""
    try:
        if len(df) < 242:
            return {
                'ts_code': ts_code,
                'close': None,
                'MA20': None,
                'MA60': None,
                'MA240': None,
                'RSI6': None,
                'RSI13': None,
                'VOL_MA3': None,
                'VOL_MA18': None,
                'relative_height': None,
                'passed': False,
                'reason': '99'  # Insufficient data
            }
        
        df = analyzer.calculate_indicators(df)
        result = analyzer.check_conditions(df)
        passed = result == 0
        reason = str(result)  # 0 (pass), 1-5 (failed condition), 99 (insufficient data)
        
        latest = df.iloc[-1]
        return {
            'ts_code': ts_code,
            'close': round(latest['close'], 2),
            'MA20': round(latest['MA20'], 2),
            'MA60': round(latest['MA60'], 2),
            'MA240': round(latest['MA240'], 2),
            'RSI6': round(latest['RSI6'], 2),
            'RSI13': round(latest['RSI13'], 2),
            'VOL_MA3': round(latest['VOL_MA3'], 2),
            'VOL_MA18': round(latest['VOL_MA18'], 2),
            'relative_height': round(latest['relative_height'], 2) if 'relative_height' in df else None,
            'passed': passed,
            'reason': reason
        }
    except Exception as e:
        return {
            'ts_code': ts_code,
            'close': None,
            'MA20': None,
            'MA60': None,
            'MA240': None,
            'RSI6': None,
            'RSI13': None,
            'VOL_MA3': None,
            'VOL_MA18': None,
            'relative_height': None,
            'passed': False,
            'reason': f'Error: {str(e)}'
        }

class StockScreener:
    def __init__(self, daily_db_path):
        self.daily_db = daily_db_path
        self.analyzer = TechnicalAnalyzer()
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging."""
        log_dir = 'data/logs'
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            filename=os.path.join(log_dir, 'screening.log'),
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s',
            delay=True
        )

    def run_screening(self, progress_callback=None):
        """Run stock screening process and record results for all stocks."""
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
            total = len(ts_codes)
            
            # Batch query all stocks
            conn = sqlite3.connect(self.daily_db)
            ts_codes_str = ','.join(f"'{code}'" for code in ts_codes)
            df_all = pd.read_sql(
                f"SELECT * FROM daily_data WHERE ts_code IN ({ts_codes_str}) ORDER BY ts_code, trade_date",
                conn
            )
            conn.close()
            
            # Parallel processing
            results = []
            with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
                futures = [executor.submit(process_stock, ts_code, df, self.analyzer)
                           for ts_code, df in df_all.groupby('ts_code')]
                for idx, future in enumerate(futures, 1):
                    results.append(future.result())
                    if progress_callback:
                        progress_callback(idx / total * 100)
            
            # Include stocks not found in database
            processed_codes = set(result['ts_code'] for result in results)
            for ts_code in ts_codes:
                if ts_code not in processed_codes:
                    results.append({
                        'ts_code': ts_code,
                        'relative_height': None,
                        'close': None,
                        'MA20': None,
                        'MA60': None,
                        'MA240': None,
                        'RSI6': None,
                        'RSI13': None,
                        'VOL_MA3': None,
                        'VOL_MA18': None,
                        'passed': False,
                        'reason': '99'  # No data in database
                    })
            
            # Save results
            if results:
                result_df = pd.DataFrame(results)
                numeric_cols = result_df.select_dtypes(include=[np.number]).columns
                result_df[numeric_cols] = result_df[numeric_cols].round(2)
                result_df = result_df[result_df['reason'] == '0']  
                # Only include passed stocks,如果需要知道全部结果，可以去掉这一行。
                
                save_dir = "data/results"
                os.makedirs(save_dir, exist_ok=True)
                save_path = os.path.join(save_dir, f"result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
                basic_path = os.path.join('data', 'stock_basic_all.csv')
                try:
                    basic_df = pd.read_csv(basic_path, encoding='utf-8-sig')
                    merged_df = pd.merge(result_df, basic_df, on='ts_code', how='left')
                    # Fill NaN by column type
                    for col in merged_df.columns:
                        if merged_df[col].dtype in ['object', 'string']:
                            merged_df[col].fillna('未知', inplace=True)
                        elif merged_df[col].dtype in ['float64', 'int64']:
                            merged_df[col].fillna(0, inplace=True)
                    merged_df.to_csv(save_path, index=False, encoding='utf-8-sig', float_format='%.2f')
                except Exception as e:
                    logging.error(f"基础信息合并失败: {str(e)}")
                    result_df.to_csv(save_path, index=False, encoding='utf-8-sig', float_format='%.2f')
                return {'count': len(result_df[result_df['passed']]), 'path': save_path}
            return None
        except Exception as e:
            logging.error(f"Screening process failed: {str(e)}")
            raise