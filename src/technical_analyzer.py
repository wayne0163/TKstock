import pandas as pd
import numpy as np
import logging
import os

class TechnicalAnalyzer:
    def __init__(self):
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging."""
        log_dir = 'data/logs'
        os.makedirs(log_dir, exist_ok=True)
        logging.basicConfig(
            filename=os.path.join(log_dir, 'screening.log'),
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
            avg_loss6 = loss.rolling(6, min_periods=1).mean().replace(0, np.nan)
            df['RSI6'] = 100 - (100 / (1 + (avg_gain6 / avg_loss6)))
            
            avg_gain13 = gain.rolling(13, min_periods=1).mean()
            avg_loss13 = loss.rolling(13, min_periods=1).mean().replace(0, np.nan)
            df['RSI13'] = 100 - (100 / (1 + (avg_gain13 / avg_loss13)))
            
            # Volume Moving Averages
            df['VOL_MA3'] = df['vol'].rolling(3, min_periods=1).mean()
            df['VOL_MA18'] = df['vol'].rolling(18, min_periods=1).mean()
            
            return df.dropna()
        except Exception as e:
            logging.error(f"Indicator calculation failed: {str(e)}")
            raise

    def check_conditions(self, df):
        """Check screening conditions, return 0 (pass) or failed condition number (1-5, 99)."""
        if len(df) < 242:
            return 99  # Insufficient data
        
        latest = df.iloc[-1]
        
        # Condition 1: MA240 rising
        cond1 = latest['MA240'] > df['MA240'].iloc[-2]
        if not cond1:
            return 1
        
        # Condition 2: Latest price > 110% of 240 days ago
        cond2 = latest['close'] > df['close'].iloc[-240] * 1.1
        if not cond2:
            return 2
        
        # Condition 3: MA60 or MA20 rising
        cond3 = (latest['MA60'] > df['MA60'].iloc[-2]) or (latest['MA20'] > df['MA20'].iloc[-2])
        if not cond3:
            return 3
        
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
            return 4
        
        # Condition 5: RSI
        cond5 = (latest['RSI13'] > 50) and (latest['RSI6'] > 70)
        if not cond5:
            return 5
        
        return 0  # Pass