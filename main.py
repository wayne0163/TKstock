import pandas as pd
import data_manager
import tech_analyzer
import streamlit as st
import time
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    
    # 使用两列布局
    col_setting, col_chart = st.columns([1, 3])
    
    with col_setting:
        with st.expander("⚙️ 基本参数", expanded=True):
            input_method = st.radio("输入方式", ["单个股票", "CSV文件"], index=0)
            
            if input_method == "单个股票":
                stock_code = st.text_input("股票代码", value="600519", help="请输入完整代码如600519.SH")
                stock_list = [stock_code] if stock_code else []
            else:
                uploaded_file = st.file_uploader("上传股票池CSV", type=["csv"])
                if uploaded_file:
                    df = pd.read_csv(uploaded_file)
                    stock_list = df['ts_code'].tolist() if 'ts_code' in df.columns else []
                else:
                    stock_list = []
            
            start_date = st.date_input("开始日期", value=datetime.now() - timedelta(days=365))
            end_date = st.date_input("结束日期", value=datetime.now())
            
        with st.expander("📈 技术指标"):
            ma_periods = st.multiselect("移动平均线", [20, 60, 240], default=[20, 60, 240])
            rsi_period = st.selectbox("RSI周期", [6, 13, ], index=0)
            show_volume = st.checkbox("显示成交量", value=True)
            
        if 'current_stock_index' not in st.session_state:
            st.session_state.current_stock_index = 0
        
        if len(stock_list) > 1:
            col_prev, _, col_next = st.columns([2,6,2])
            with col_prev:
                if st.button("← 上一只"):
                    st.session_state.current_stock_index = max(0, st.session_state.current_stock_index - 1)
            with col_next:
                if st.button("下一只 →"):
                    st.session_state.current_stock_index = min(len(stock_list)-1, st.session_state.current_stock_index + 1)
    
    with col_chart:
        if st.button('生成图表', type='primary'):
            st.session_state.chart_generated = True
        
        if st.session_state.get('chart_generated'):
            def generate_chart():
                try:
                    # 原有图表生成逻辑
                    current_code = stock_list[st.session_state.current_stock_index]
                    
                    # 调用新模块生成图表
                    from kline_manager import generate_chart
                    processed_code = current_code
                    if '.' not in processed_code:
                        if processed_code.startswith('6'):
                            processed_code += '.SH'
                        elif processed_code.startswith(('0', '2')):
                            processed_code += '.SZ'
                        elif processed_code.startswith('8'):
                            processed_code += '.BJ'
                        else:
                            st.warning("股票代码格式错误，请输入完整代码如600519.SH")
                            return
                    fig, df = generate_chart(
                        stock_code=processed_code,
                        start_date=start_date.strftime('%Y%m%d'),
                        end_date=end_date.strftime('%Y%m%d'),
                        ma_periods=ma_periods,
                        rsi_periods=[rsi_period],
                        show_volume=show_volume
                    )

                    if not fig:
                        st.warning(df)  # 此处df为错误信息
                        return

                    # 调整图表容器样式
                    st.markdown(f'<div style="margin-bottom: 35px;">', unsafe_allow_html=True)
                    st.plotly_chart(fig, use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # 显示当前股票序号
                    # 轮播控制按钮
                    if len(stock_list) > 1:
                        col1, col2 = st.columns([1,3])
                        with col1:
                            if st.button('← 上一只', use_container_width=True):
                                st.session_state.current_stock_index = (st.session_state.current_stock_index - 1) % len(stock_list)
                        with col2:
                            if st.button('下一只 →', use_container_width=True):
                                st.session_state.current_stock_index = (st.session_state.current_stock_index + 1) % len(stock_list)
                        
                        st.write(f"当前展示：{st.session_state.current_stock_index+1}/{len(stock_list)} ({processed_code})")
                    
                    # 显示最新数据摘要
                    with st.expander("最新数据概览"):
                        st.dataframe(
                            df.tail(10)[['trade_date', 'open', 'close', 'high', 'low', 'vol']]
                            .style.background_gradient(cmap='Blues')
                        )

                except Exception as e:
                    st.error(f"图表生成失败: {str(e)}")
                
                # 监听参数变化自动重置索引
                current_params = (ma_periods, rsi_period, start_date, end_date)
                if 'last_params' not in st.session_state or st.session_state.last_params != current_params:
                    st.session_state.current_stock_index = 0
                    st.session_state.last_params = current_params
        
        # 参数变更时重置生成状态
        if 'last_params' in st.session_state and st.session_state.last_params != current_params:
            st.session_state.chart_generated = False

            # 添加样式说明
            st.markdown("""
            <style>
            div[data-testid="stExpander"] div[role="button"] p {
                font-size: 1.2rem;
                font-weight: 600;
            }
            </style>
            """, unsafe_allow_html=True)

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

            generate_chart()
