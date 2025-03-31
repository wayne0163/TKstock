import os
import sqlite3
import pandas as pd
import tushare as ts
import configparser
import os

def read_config(config_path='config/settings.ini'):
    config = configparser.ConfigParser()
    try:
        if os.path.exists(config_path):
            config.read(config_path)
            return config
        else:
            raise FileNotFoundError(f'配置文件 {config_path} 不存在')
    except Exception as e:
        raise RuntimeError(f'读取配置文件失败: {str(e)}')
from datetime import datetime, timedelta
import configparser

def init_db(db_path):
    """初始化数据库"""
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建股票日线数据表
    cursor.execute('''CREATE TABLE IF NOT EXISTS daily_data
                     (ts_code TEXT, trade_date TEXT, open REAL, high REAL, low REAL, 
                      close REAL, pre_close REAL, change REAL, pct_chg REAL, 
                      vol REAL, amount REAL, PRIMARY KEY (ts_code, trade_date))''')
    
    # 创建财务指标数据表
    cursor.execute('''CREATE TABLE IF NOT EXISTS fina_indicator
                     (ts_code TEXT, end_date TEXT, roe_dt REAL, or_yoy REAL, 
                      op_yoy REAL, PRIMARY KEY (ts_code, end_date))''')
    
    # 创建每日指标数据表
    cursor.execute('''CREATE TABLE IF NOT EXISTS daily_basic
                     (ts_code TEXT, trade_date TEXT, close REAL, turnover_rate REAL, 
                      turnover_rate_f REAL, volume_ratio REAL, pe REAL, pe_ttm REAL, 
                      pb REAL, ps REAL, ps_ttm REAL, dv_ratio REAL, dv_ttm REAL, 
                      total_share REAL, float_share REAL, free_share REAL, 
                      total_mv REAL, circ_mv REAL, PRIMARY KEY (ts_code, trade_date))''')
    
    conn.commit()
    conn.close()

def read_config():
    config = configparser.ConfigParser()
    config.read('config/settings.ini')
    return config


def get_database_stats(db_path):
    """获取数据库统计信息"""
    stats = {}
    try:
        conn = sqlite3.connect(db_path)
        
        # 统计daily_data表
        daily_stats = {}
        # 统计daily_data表
        df = pd.read_sql("SELECT MIN(trade_date) as min_date, MAX(trade_date) as max_date FROM daily_data", conn)
        daily_stats.update(df.iloc[0].to_dict() if not df.empty else {'min_date': 'N/A', 'max_date': 'N/A'})
        
        df = pd.read_sql("SELECT COUNT(DISTINCT ts_code) as stock_count FROM daily_data", conn)
        daily_stats['stock_count'] = df.iloc[0]['stock_count'] if not df.empty else 0
        stats['daily_data'] = daily_stats
        
        # 统计fina_indicator表
        fina_stats = {}
        df = pd.read_sql("SELECT MIN(end_date) as min_year, MAX(end_date) as max_year FROM fina_indicator", conn)
        fina_stats.update(df.iloc[0].to_dict() if not df.empty else {'min_year': 'N/A', 'max_year': 'N/A'})
        stats['fina_indicator'] = fina_stats
        
        # 统计daily_basic表
        basic_stats = {}
        df = pd.read_sql("SELECT MIN(trade_date) as min_date, MAX(trade_date) as max_date FROM daily_basic", conn)
        basic_stats.update(df.iloc[0].to_dict() if not df.empty else {'min_date': 'N/A', 'max_date': 'N/A'})
        stats['daily_basic'] = basic_stats
        
        conn.close()
    except Exception as e:
        print(f"获取统计信息失败: {str(e)}")
        return None
    
    return stats

def download_daily_data(db_path=None, token=None, update_progress=None):
    config = read_config()
    db_path = db_path or config['Database']['daily_db']
    token = token or config['API']['tushare_token']
    
    ts.set_token(token)
    pro = ts.pro_api()
    
    if not os.path.exists(db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        init_db(db_path)
    else:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_data'")
        if not cursor.fetchone():
            init_db(db_path)
        conn.close()
    
    # 如果未提供回调函数则使用空函数
    if update_progress is None:
        def update_progress(progress, message):
            pass
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取最新交易日期
    cursor.execute("SELECT MAX(trade_date) FROM daily_data")
    last_date = cursor.fetchone()[0]
    
    # 计算日期范围
    end_date = datetime.now().strftime('%Y%m%d')
    if last_date is None:
        trade_cal = pro.trade_cal(exchange='', start_date='20100101', end_date=end_date)
        trade_dates = trade_cal[trade_cal['is_open'] == 1]['cal_date'].tolist()
        start_date = trade_dates[-400] if len(trade_dates) >= 400 else trade_dates[0]
    else:
        start_date = last_date
    
    # 获取交易日历
    trade_cal = pro.trade_cal(exchange='', start_date=start_date, end_date=end_date)
    trade_dates = trade_cal[trade_cal['is_open'] == 1]['cal_date'].tolist()
    
    # 下载数据
    total_days = len(trade_dates)
    current_day = 0
    
    def update_progress(progress, message):
        pass
    
    for date in trade_dates:
        if date >= start_date:
            current_day += 1
            progress = current_day / total_days
            update_progress(progress, f'正在下载 {date} 日线数据 ({current_day}/{total_days})')
            
            df = pro.daily(trade_date=date)
            if not df.empty:
                df = df.drop_duplicates(['ts_code', 'trade_date'])
                try:
                    df.to_sql('daily_data', conn, if_exists='append', index=False, 
                            method='multi', chunksize=1000)
                except sqlite3.IntegrityError as e:
                    print(f"跳过重复日线数据 {date}: {str(e)}")
                    continue
    
    conn.close()

def download_fina_indicator(db_path, token, update_progress=lambda progress, message: None):
    """下载财务指标数据（使用VIP接口）"""
    ts.set_token(token)
    pro = ts.pro_api()

    # 初始化数据库连接
    conn = sqlite3.connect(db_path)
    init_db(db_path)

    try:
        # 获取最新财务年度
        max_year = pd.read_sql("SELECT MAX(end_date) FROM fina_indicator", conn).iloc[0,0]
        current_year = datetime.now().year

        # 构建查询参数
        period = f"{(current_year-1)}1231" if datetime.now().month < 5 else f"{current_year}0630"
        fields = "ts_code,end_date,roe_dt,or_yoy,op_yoy"

        update_progress(0.3, '正在通过VIP接口获取财务数据')
        
        # 使用VIP接口批量获取数据
        df = pro.fina_indicator_vip(
            period=period,
            fields=fields,
            market='SSE,SZSE'  # 获取全市场数据
        )

        # 数据清洗和类型转换
        df['end_date'] = pd.to_datetime(df['end_date']).dt.strftime('%Y%m%d')
        df = df.drop_duplicates(['ts_code', 'end_date'])

        # 使用upsert方式更新数据
        update_progress(0.7, '正在更新数据库')
        df.to_sql('fina_indicator', conn, if_exists='replace', index=False,
                 method='multi')

        # 验证数据完整性
        record_count = pd.read_sql("SELECT COUNT(*) FROM fina_indicator", conn).iloc[0,0]
        if record_count < 1000:
            raise ValueError(f"数据记录异常，仅获取到{record_count}条数据")

    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"财务数据下载失败: {str(e)}")
    finally:
        conn.close()

def download_daily_basic(db_path, token, update_progress=lambda progress, message: None):
    """下载每日指标数据"""
    ts.set_token(token)
    pro = ts.pro_api()
    
    # 检查数据库是否存在
    if not os.path.exists(db_path):
        init_db(db_path)
    else:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='daily_basic'")
            if not cursor.fetchone():
                init_db(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 获取最新交易日期
    cursor.execute("SELECT MAX(trade_date) FROM daily_data")
    last_date = cursor.fetchone()[0]
    
    # 计算日期范围（修复日期逻辑）
    end_date = datetime.now().strftime('%Y%m%d')
    if last_date is None:
        trade_cal = pro.trade_cal(exchange='', start_date='20100101', end_date=end_date)
        trade_dates = trade_cal[trade_cal['is_open'] == 1]['cal_date'].tolist()
        start_date = trade_dates[-400] if len(trade_dates) >= 400 else trade_dates[0]
    else:
        # 获取最后一个已有日期的下个交易日
        next_day = pro.trade_cal(exchange='', start_date=last_date, end_date=end_date)
        next_day = next_day[next_day['is_open'] == 1]['cal_date'].tolist()
        start_date = next_day[1] if len(next_day) > 1 else end_date  # 跳过已存在的日期
        print(f"start_date: {start_date}")
    
    # 获取交易日历
    trade_cal = pro.trade_cal(exchange='', start_date=start_date, end_date=end_date)
    trade_dates = trade_cal[trade_cal['is_open'] == 1]['cal_date'].tolist()
    
    # 下载数据
    total_days = len(trade_dates)
    current_day = 0
    
    # 在下载函数开头添加去重检查
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")  # 提升写入性能
    
    for date in trade_dates:
        if date >= start_date:
            current_day += 1
            progress = current_day / total_days
            update_progress(progress, f'正在下载 {date} 每日指标 ({current_day}/{total_days})')
            
            # 获取数据后立即处理
            df = pro.daily_basic(trade_date=date)
            
            if df is not None and not df.empty:
                # 去除重复记录并插入数据库
                df = df.drop_duplicates(['ts_code', 'trade_date'])
                df.to_sql('daily_basic', conn, if_exists='append', index=False)
    
    conn.close()