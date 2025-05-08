import pandas as pd
import numpy as np
import logging

class TechnicalAnalyzer:
    def __init__(self):
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging."""
        logging.basicConfig(
            filename='data/logs/screening.log',
            level=logging.ERROR,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def calculate_indicators(self, df):
        """Calculate technical indicators."""
        try:
            df = df.copy()
            # Moving Averages
            df['MA20'] = df['close'].rolling(20, min_periods=1).mean()
            df['MA60'] = df['close'].rolling(60, min_periods=1).mean()
            df['MA240'] = df['close'].rolling(240, min_periods=1).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            avg_gain6 = gain.rolling(6, min_periods=1).mean()
            avg_loss6 = loss.rolling(6, min_periods=1).mean()
            # 避免除零错误，使用 np.where 处理
            df['RSI6'] = np.where(avg_loss6 != 0, 100 - (100 / (1 + (avg_gain6 / avg_loss6))), 100)
            
            avg_gain13 = gain.rolling(13, min_periods=1).mean()
            avg_loss13 = loss.rolling(13, min_periods=1).mean()
            df['RSI13'] = np.where(avg_loss13 != 0, 100 - (100 / (1 + (avg_gain13 / avg_loss13))), 100)
            
            # Volume Moving Averages
            df['VOL_MA3'] = df['vol'].rolling(3, min_periods=1).mean()
            df['VOL_MA18'] = df['vol'].rolling(18, min_periods=1).mean()
            
            return df.dropna()
        except Exception as e:
            logging.error(f"Indicator calculation failed: {str(e)}")
            raise

    def check_conditions(self, df):
        """Check screening conditions and return result code."""
        try:
            if len(df) < 242:
                return pd.DataFrame([{'result': 99, 'reason': 'Insufficient data length'}])
            
            latest = df.iloc[-1]
            
            # Condition 1: MA240 rising
            cond1 = latest['MA240'] > df['MA240'].iloc[-2]
            if not cond1:
                return pd.DataFrame([{'result': 1, 'reason': 'MA240 not rising'}])
            
            # Condition 2: Latest price > 110% of 240 days ago
            cond2 = latest['close'] > df['close'].iloc[-240] * 1.1
            if not cond2:
                return pd.DataFrame([{'result': 2, 'reason': 'Price not above 110% of 240 days ago'}])
            
            # Condition 3: MA60 or MA20 rising
            cond3 = (latest['MA60'] > df['MA60'].iloc[-2]) or (latest['MA20'] > df['MA20'].iloc[-2])
            if not cond3:
                return pd.DataFrame([{'result': 3, 'reason': 'MA60 or MA20 not rising'}])
            
            # Condition 4: Volume crossover and trend
            cond4 = False
            for i in range(-3, 0):
                if (df['VOL_MA3'].iloc[i] > df['VOL_MA18'].iloc[i]) and \
                   (df['VOL_MA3'].iloc[i-1] <= df['VOL_MA18'].iloc[i-1]):
                    cond4 = True
                    break
            vol_ma3_up = (df['VOL_MA3'].iloc[-1] > df['VOL_MA3'].iloc[-2]) and \
                         (df['VOL_MA3'].iloc[-2] > df['VOL_MA3'].iloc[-3])
            vol_ma18_up = (df['VOL_MA18'].iloc[-1] > df['VOL_MA18'].iloc[-2]) and \
                          (df['VOL_MA18'].iloc[-2] > df['VOL_MA18'].iloc[-3])
            cond4 = cond4 and vol_ma3_up and vol_ma18_up
            if not cond4:
                return pd.DataFrame([{'result': 4, 'reason': 'Volume conditions not met'}])
            
            # Condition 5: RSI
            cond5 = (latest['RSI13'] > 50) and (latest['RSI6'] > 70)
            if not cond5:
                return pd.DataFrame([{'result': 5, 'reason': 'RSI conditions not met'}])
            
            # All conditions passed
            return pd.DataFrame([{'result': 0, 'reason': 'All conditions passed'}])
        except Exception as e:
            logging.error(f"Condition check failed: {str(e)}")
            return pd.DataFrame([{'result': -1, 'reason': f'Error: {str(e)}'}])