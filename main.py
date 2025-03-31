import data_manager
import tech_analyzer
import streamlit as st
import time

# 主界面框架
st.title("A股股票决策系统")

# 侧边栏导航菜单
with st.sidebar:
    menu = st.selectbox("功能菜单", 
        ["数据管理", "技术分析", "K线图", "回测系统", "交易分析"])

# 各模块功能实现
if menu == "数据管理":
    # 数据库配置区域
    try:
            config = data_manager.read_config()
            db_path = config['Database']['daily_db']
            api_token = config['API']['tushare_token']
    except Exception as e:
            st.error(f"配置读取失败: {str(e)}")
            st.stop()
    
    # 数据操作功能区
    st.subheader("数据下载")
    col1, col2, col3 = st.columns(3)
    
    # 交易数据下载
    with col1:
        if st.button("下载交易数据"):
            try:
                progress_bar = st.progress(0)
                data_manager.download_daily_data(db_path, api_token, 
                    lambda p, m: progress_bar.progress(p))
                st.success("交易数据下载完成")
            except Exception as e:
                st.error(f"下载失败: {str(e)}")
    
    # 财务数据下载        
    with col2:
        if st.button("下载财务数据"):
            try:
                progress_bar = st.progress(0)
                data_manager.download_fina_indicator(db_path, api_token,
                    lambda p, m: progress_bar.progress(p))
                st.success("财务数据下载完成")
            except Exception as e:
                st.error(f"下载失败: {str(e)}")
    
    # 每日指标下载
    with col3:
        if st.button("下载每日指标"):
            try:
                progress_bar = st.progress(0)
                data_manager.download_daily_basic(db_path, api_token,
                    lambda p, m: progress_bar.progress(p))
                st.success("每日指标下载完成")
            except Exception as e:
                st.error(f"下载失败: {str(e)}")

    # 统计信息展示
    st.subheader("数据库统计")
    if st.button("刷新统计信息"):
        try:
            stats = data_manager.get_database_stats(db_path)
            if stats:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    with st.expander("日线数据统计"):
                        st.write(f"最早日期: {stats['daily_data']['min_date'][:4]}-{stats['daily_data']['min_date'][4:6]}-{stats['daily_data']['min_date'][6:]}")
                        st.write(f"最新日期: {stats['daily_data']['max_date'][:4]}-{stats['daily_data']['max_date'][4:6]}-{stats['daily_data']['max_date'][6:]}")
                        st.write(f"股票数量: {stats['daily_data']['stock_count']}")
                
                with col2:
                    with st.expander("财务指标统计"):
                        st.write(f"最早年度: {stats['fina_indicator']['min_year'][:4]}")
                        st.write(f"最新年度: {stats['fina_indicator']['max_year'][:4]}")
                
                with col3:
                    with st.expander("每日指标统计"):
                        st.write(f"最早日期: {stats['daily_basic']['min_date'][:4]}-{stats['daily_basic']['min_date'][4:6]}-{stats['daily_basic']['min_date'][6:]}")
                        st.write(f"最新日期: {stats['daily_basic']['max_date'][:4]}-{stats['daily_basic']['max_date'][4:6]}-{stats['daily_basic']['max_date'][6:]}")
            else:
                st.warning("数据库统计信息获取失败")
            
            # 显示总览信息
            st.write(f"已收录股票数：{stats['daily_data']['stock_count']} 只")
            st.write(f"最近更新日期：{stats['daily_data']['max_date']}")
        except Exception as e:
            st.error(f"统计异常: {str(e)}")

elif menu == "技术分析":
    # 股票池上传
    uploaded_file = st.file_uploader("上传股票池CSV", type=["csv"])
    stock_pool = []
    if uploaded_file:
        stock_pool = tech_analyzer.load_stock_pool(uploaded_file)
    
    # 市值筛选设置
    with st.expander("市值范围设置"):
        col1, col2 = st.columns(2)
        with col1:
            min_mv = st.number_input("最小市值(万元)", value=200000)
        with col2:
            max_mv = st.number_input("最大市值(万元)", value=3000000)
    
    col_btn, col_stats = st.columns([2,3])
    with col_btn:
        if st.button("执行五步筛选"):
            try:
                config = data_manager.read_config()
                db_path = config['Database']['daily_db']
                filename, result_df, pool_count = tech_analyzer.screen_stocks(stock_pool, db_path, max_mv, min_mv)
                
                with col_stats:
                    st.metric("合并后候选股票池数量", f"{pool_count} 支")
                    if result_df is not None:
                        st.success(f"筛选完成，共找到{len(result_df)}只股票")
                        st.dataframe(result_df)
                        with open(filename, "rb") as f:
                            st.download_button("下载结果", f, file_name=filename)
                    else:
                        st.warning("没有找到符合条件的股票")
            except Exception as e:
                st.error(f"筛选失败: {str(e)}")
    


elif menu == "K线图":
    st.subheader("K线图分析")
    with st.expander("参数设置"):
        stock_code = st.text_input("股票代码", value="600519")
        date_range = st.date_input("日期范围", [])
    
    if st.button("生成图表"):
        st.warning("功能开发中，预计下个版本上线")

elif menu == "回测系统":
    st.subheader("策略回测")
    with st.form("backtest_form"):
        capital = st.number_input("初始资金(万元)", value=100.0)
        start_date = st.date_input("回测开始日期")
        
        if st.form_submit_button("执行回测"):
            st.error("回测模块需要集成Backtrader，当前暂未实现")

elif menu == "交易分析":
    st.subheader("持仓分析")
    uploaded_trades = st.file_uploader("上传交易记录", type=["csv"])
    if uploaded_trades:
        st.info("交易分析模块需要对接持仓数据库，当前仅支持CSV预览")
        st.dataframe(pd.read_csv(uploaded_trades).head())