import sqlite3
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def get_hist_data(ts_code, start_date=None, end_date=None):
    """从数据库获取股票历史数据"""
    try:
        # 自动补全股票代码后缀
        if '.' not in ts_code:
            if ts_code.startswith('6'):
                ts_code += '.SH'
            elif ts_code.startswith(('0', '2')):
                ts_code += '.SZ'
            elif ts_code.startswith('8'):
                ts_code += '.BJ'

        from data_manager import read_config
        config = read_config()
        conn = sqlite3.connect(config['Database']['daily_db'])
        
        # 检查表是否存在
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_data'")
        if not cursor.fetchone():
            return pd.DataFrame(), "请先下载股票交易数据"
        
        # 获取默认日期范围
        cursor = conn.cursor()
        cursor.execute("""
            SELECT MIN(trade_date), MAX(trade_date) 
            FROM daily_data 
            WHERE ts_code = ?
        """, (ts_code,))
        min_date, max_date = cursor.fetchone()
        
        # 处理默认日期参数
        start_date = start_date or min_date
        end_date = end_date or max_date
        
        # 参数化查询防止SQL注入
        query = """
        SELECT trade_date, open, high, low, close, vol
        FROM daily_data
        WHERE ts_code = ?
        AND trade_date BETWEEN ? AND ?
        ORDER BY trade_date
        """
        df = pd.read_sql(query, conn, params=(ts_code, start_date, end_date))
        conn.close()
        return df
    except Exception as e:
        print(f"获取历史数据失败: {str(e)}")
        return pd.DataFrame()

def calculate_indicators(df, ma_periods=[20, 60, 240], rsi_periods=[6, 13]):
    """计算多周期技术指标"""
    try:
        # 计算移动平均线
        for period in ma_periods:
            df[f'MA{period}'] = df['close'].rolling(period).mean()
        
        # 计算RSI指标
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        for period in rsi_periods:
            avg_gain = gain.rolling(period).mean()
            avg_loss = loss.rolling(period).mean()
            rs = avg_gain / avg_loss
            df[f'RSI{period}'] = 100 - (100 / (1 + rs))
        
        return df
    except Exception as e:
        print(f"指标计算失败: {str(e)}")
        return df

def generate_chart(stock_code, start_date=None, end_date=None, ma_periods=[20, 60, 240], rsi_periods=[6, 13], show_volume=True):
    """生成Plotly图表"""
    try:
        # 获取历史数据（自动应用默认日期范围）
        df = get_hist_data(stock_code, start_date, end_date)
        if df.empty:
            return pd.DataFrame(), f"未找到{ts_code}的历史数据，请检查代码或日期范围"
        
        # 数据长度校验
        if len(df) < 240:
            return None, "需要至少240个交易日数据来计算长期指标"
        
        # 计算技术指标
        df = calculate_indicators(df, ma_periods=ma_periods, rsi_periods=[6, 13])
        
        # 创建图表
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                          vertical_spacing=0.05,
                          row_heights=[0.7, 0.3])
        
        # K线主图
        fig.add_trace(go.Candlestick(x=df['trade_date'],
                                    open=df['open'],
                                    high=df['high'],
                                    low=df['low'],
                                    close=df['close'],
                                    name='K线'), row=1, col=1)
        
        # 移动平均线
        # 添加多周期均线
        for period in [20, 60, 240]:
            fig.add_trace(go.Scatter(x=df['trade_date'],
                                   y=df[f'MA{period}'],
                                   line=dict(width=2),
                                   name=f'{period}日均线'),
                        row=1, col=1)
        
        # RSI指标
        # RSI指标
        fig.add_trace(go.Scatter(x=df['trade_date'], y=df['RSI6'],
                               line=dict(color='blue'),
                               name='RSI6'),
                    row=2, col=1)
        
        fig.add_trace(go.Scatter(x=df['trade_date'], y=df['RSI13'],
                               line=dict(color='purple', dash='dot'),
                               name='RSI13'),
                    row=2, col=1)
        
        # 成交量
        if show_volume:
            fig.add_trace(go.Bar(x=df['trade_date'], y=df['vol'],
                               marker_color='rgba(0,128,0,0.5)',
                               name='成交量'),
                        row=2, col=1)
        
        # 图表布局设置
        fig.update_layout(
            height=800,
            title=f'{stock_code} 股票分析',
            xaxis_rangeslider_visible=False,
            hovermode='x unified'
        )
        return fig, df
    except Exception as e:
        return None, f"图表生成失败: {str(e)}"