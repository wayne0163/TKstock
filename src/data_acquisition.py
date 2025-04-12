import tushare as ts
import pandas as pd
import logging

class DataAcquisition:
    def __init__(self, tushare_token):
        """Initialize Tushare API."""
        self.token = tushare_token
        ts.set_token(tushare_token)
        self.pro = ts.pro_api()
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging."""
        logging.basicConfig(
            filename='data/logs/data_update.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def get_trade_calendar(self, start_date, end_date):
        """Get trading calendar."""
        try:
            trade_cal = self.pro.trade_cal(
                start_date=start_date,
                end_date=end_date,
                is_open=1
            )
            trade_cal['cal_date'] = pd.to_datetime(trade_cal['cal_date'], format='%Y%m%d')
            return trade_cal
        except Exception as e:
            logging.error(f"Failed to fetch trade calendar: {str(e)}")
            return None

    def get_daily_data(self, trade_date):
        """Fetch daily data for a specific date."""
        try:
            df_daily = self.pro.daily(
                trade_date=trade_date,
                fields='ts_code,trade_date,open,low,high,close,vol'
            )
            df_basic = self.pro.daily_basic(
                trade_date=trade_date,
                fields='ts_code,trade_date,pe_ttm,pb,total_mv'
            )
            if df_daily is None or df_basic is None:
                return None
            merged = pd.merge(df_daily, df_basic, on=['ts_code', 'trade_date'], how='left')
            return merged.fillna(value=0)
        except Exception as e:
            logging.error(f"Failed to fetch daily data for {trade_date}: {str(e)}")
            return None

    def get_stock_basic(self):
        """获取全市场上市公司基础信息"""
        try:
            pro = ts.pro_api(self.token)
            df = pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,name,industry'
            )
            return df.dropna(subset=['ts_code'])
        except Exception as e:
            print(f"获取上市公司数据失败: {str(e)}")
            return None