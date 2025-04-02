import sqlite3
import pandas as pd
import tushare as ts
from datetime import datetime
import streamlit as st
import data_manager

def load_stock_pool(uploaded_file):
    """处理上传的股票池csv文件"""
    try:
        df = pd.read_csv(uploaded_file)
        if 'ts_code' not in df.columns:
            st.error('CSV文件必须包含ts_code字段')
            return None
        return df['ts_code'].unique().tolist()
    except Exception as e:
        st.error(f'文件读取失败: {str(e)}')
        return None

def get_daily_basic_data(db_path, trade_date):
    """从数据库获取最新交易日的daily_basic数据"""
    conn = sqlite3.connect(db_path)
    query = f"""
    SELECT ts_code,total_mv 
    FROM daily_basic 
    WHERE trade_date = (SELECT MAX(trade_date) FROM daily_basic)
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def calculate_technical_indicators(ts_code, db_path):
    """计算个股技术指标"""
    conn = sqlite3.connect(db_path)
    try:
        # 获取个股历史数据
        df = pd.read_sql("""
            SELECT trade_date,close,vol 
            FROM daily_data 
            WHERE ts_code=? 
            ORDER BY trade_date DESC
            LIMIT 242
            """, conn, params=(str(ts_code),))
        
        if len(df) < 242:
            return None

        # 计算移动平均
        df['MA20'] = df['close'].rolling(20).mean()
        df['MA60'] = df['close'].rolling(60).mean()
        df['MA240'] = df['close'].rolling(240).mean()
    
        # 添加240天前收盘价
        df['close_240d_ago'] = df['close'].shift(240)
        
        # 计算RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain6 = gain.rolling(6).mean()
        avg_loss6 = loss.rolling(6).mean()
        df['RSI6'] = 100 - (100 / (1 + avg_gain6 / avg_loss6))
        
        avg_gain13 = gain.rolling(13).mean()
        avg_loss13 = loss.rolling(13).mean()
        df['RSI13'] = 100 - (100 / (1 + avg_gain13 / avg_loss13))

        # 计算成交量均线
        df['VOL_MA3'] = df['vol'].rolling(3).mean()
        df['VOL_MA18'] = df['vol'].rolling(18).mean()
        
        return df  # 返回完整DataFrame

    except Exception as e:
        st.error(f'计算技术指标失败: {str(e)}')
        return None
    finally:
        conn.close()

def screen_stocks(stock_list, db_path, max_mv, min_mv) -> tuple:
    """执行五步筛选条件"""
    config = data_manager.read_config()
    token = config['API']['tushare_token']
    ts.set_token(token)
    pro = ts.pro_api()
    
    # 获取最新交易日
    trade_date = pro.trade_cal(exchange='', end_date=datetime.now().strftime('%Y%m%d'), is_open='1').iloc[-1]['cal_date']
    
    # 获取市值筛选结果
    mv_df = get_daily_basic_data(db_path, trade_date)
    mv_selected = mv_df[(mv_df['total_mv'] >= min_mv) & (mv_df['total_mv'] <= max_mv)]['ts_code'].tolist()
    
    # 合并股票池
    final_pool = list(set(stock_list + mv_selected))
    st.write(f'初始股票池数量: {len(stock_list)}')
    st.write(f'市值筛选数量: {len(mv_selected)}')
    st.write(f'合并后候选池数量: {len(final_pool)}')

    results = []
    for ts_code in final_pool:
        # 获取技术指标数据
        df_tech = calculate_technical_indicators(ts_code, db_path)
        if df_tech is None or len(df_tech) < 2:
            continue

        # 条件1: MA240向上（最新MA240 > 昨日MA240）
        # 确保DataFrame有足够行数
        if len(df_tech) < 2:
            continue
        
        # 条件1: MA240向上（最新MA240 > 昨日MA240）
        cond1 = df_tech['MA240'].iloc[-1] > df_tech['MA240'].iloc[-2]
        
        # 条件2: 最新价 > 240天前价格的110%
        cond2 = df_tech['close'].iloc[-1] > df_tech['close_240d_ago'].iloc[-1] * 1.1
        
        # 条件3: MA趋势（60日或20日均线上扬）
        cond3 = (df_tech['MA60'].iloc[-1] > df_tech['MA60'].iloc[-2]) or \
                (df_tech['MA20'].iloc[-1] > df_tech['MA20'].iloc[-2])
        
        # 条件4: 成交量交叉检测（3日均线上穿18日均线）
        cond4 = (df_tech['VOL_MA3'].iloc[-1] > df_tech['VOL_MA18'].iloc[-1]) and \
                (df_tech['VOL_MA3'].iloc[-2] <= df_tech['VOL_MA18'].iloc[-2])
        
        # 条件5: RSI指标
        cond5 = (df_tech['RSI13'].iloc[-1] > 50) and (df_tech['RSI6'].iloc[-1] > 70)
        
        if all([cond1, cond2, cond3, cond4, cond5]):
            
            stock_info = pro.stock_basic(ts_code=ts_code, fields='ts_code,name,industry')
            # 增加有效性检查
            if not stock_info.empty and len(stock_info) > 0:
                results.append({
                    'ts_code': ts_code,
                    'name': stock_info['name'].values[0],
                    'industry': stock_info['industry'].values[0],
                    'current_price': df_tech['close'].iloc[-1],
                    'MA240_trend': '上升' if cond1 else '下降'
                })
    
    result_df = pd.DataFrame(results)
    if not result_df.empty:
        conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(trade_date) FROM daily_data")
    latest_date = cursor.fetchone()[0]
    conn.close()
    
    filename = f'result_{latest_date}.csv'
    result_df.to_csv(filename, index=False)
    return filename, result_df, len(final_pool)
    return None, None, 0