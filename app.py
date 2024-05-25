import pandas as pd
import numpy as np
from flask import Flask, render_template, request, jsonify
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
import random

from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

from flask import Flask, jsonify, render_template, request, abort, flash, redirect, session
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from function import hash_code
from flask_bootstrap import Bootstrap
import numpy as np
import sqlite3
import os

app = Flask(__name__)
bootstrap = Bootstrap(app)

# 读取Excel数据
def load_data():
    return pd.read_excel('data/testdata.xlsx', header=1)


# 计算移动平均线
def moving_average(data, window):
    return data.rolling(window=window).mean()


# 计算MACD指标
def macd(data, short_period, long_period, signal_period):
    short_ema = data.ewm(span=short_period, adjust=False).mean()
    long_ema = data.ewm(span=long_period, adjust=False).mean()
    macd_line = short_ema - long_ema
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    return macd_line, signal_line


@app.route('/')
def index():
    return render_template('login.html')

@app.route('/home')
def index2():
    return render_template('index.html')

@app.route('/api/adduser', methods=['GET', 'POST'])
def add_user():
    if request.json:
        username = request.json.get('username', '').strip()
        password = request.json.get('password')
        confirm_password = request.json.get('confirm')
        # 判断所有输入都不为空
        if username and password and confirm_password:
            if password != confirm_password:
                return jsonify({'code': '400', 'msg': '两次密码不匹配！'}), 400
            # 连接数据  库
            conn = sqlite3.connect('db.db')
            cur = conn.cursor()
            # 查询输入的用户名是否已经存在
            sql_same_user = 'SELECT 1 FROM USER WHERE USERNAME=?'
            same_user = cur.execute(sql_same_user, (username,)).fetchone()
            if same_user:
                return jsonify({'code': '400', 'msg': '用户名已存在'}), 400
            # 通过检查的数据，插入数据库表中
            sql_insert_user = 'INSERT INTO USER(USERNAME, PASSWORD) VALUES (?,?)'
            cur.execute(sql_insert_user, (username, hash_code(password)))
            conn.commit()
            sql_new_user = 'SELECT id,username FROM USER WHERE USERNAME=?'
            user_id, user = cur.execute(sql_new_user, (username,)).fetchone()
            conn.close()
            return jsonify({'code': '200', 'msg': '账号生成成功！', 'newUser': {'id': user_id, 'user': user}})
        else:

            return jsonify({'code': '404', 'msg': '请求参数不全!'})
    else:
        abort(400)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 获取请求中的数据
        username = request.form.get('username')
        password = hash_code(request.form.get('password'))

        # 连接数据库，判断用户名+密码组合是否匹配
        conn = sqlite3.connect('db.db')
        cur = conn.cursor()
        try:
            sql = 'SELECT college, gender, cet_score FROM USER WHERE USERNAME=? AND PASSWORD=?'
            user_info = cur.execute(sql, (username, password)).fetchone()

        except:
            flash('用户名或密码错误！')
            return render_template('login.html')
        finally:
            conn.close()

        if user_info is not None:
            return render_template('index.html')
        else:
            flash('用户名或密码错误！')
            return render_template('login.html')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm')
        # 判断所有输入都不为空
        if username and password and confirm_password:
            if password != confirm_password:
                flash('两次输入的密码不一致！')
                return render_template('register.html', username=username)
            # 连接数据库
            conn = sqlite3.connect('db.db')
            cur = conn.cursor()
            # 查询输入的用户名是否已经存在
            sql_same_user = 'SELECT 1 FROM USER WHERE USERNAME=?'
            same_user = cur.execute(sql_same_user, (username,)).fetchone()
            if same_user:
                flash('用户名已存在！')
                return render_template('register.html', username=username)
            # 通过检查的数据，插入数据库表中
            sql_insert_user = 'INSERT INTO USER(USERNAME, PASSWORD) VALUES (?,?)'
            cur.execute(sql_insert_user, (username, hash_code(password)))
            conn.commit()
            conn.close()
            # 重定向到登录页面
            return redirect('/login')
        else:
            flash('所有字段都必须输入！')
            if username:
                return render_template('register.html', username=username)
            return render_template('register.html')
    return render_template('register.html')

@app.route('/logout')
def logout():
    # 退出登录，清空session
    if session.get('is_login'):
        session.clear()
        return redirect('/')
    return redirect('/')


@app.route('/visualize')
def visualize():
    data = load_data()

    # 数据预处理
    data['收盘到期收益率(%)'] = pd.to_numeric(data['收盘到期收益率(%)'], errors='coerce')
    data.dropna(subset=['收盘到期收益率(%)'], inplace=True)

    # 描述性统计分析
    stats = data['收盘到期收益率(%)'].describe().round(2)
    stats.index = ['样本数', '均值', '标准差', '最小值', '25%分位数', '中位数', '75%分位数', '最大值']


    # 生成时间序列
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2024, 12, 31)
    dates = pd.date_range(start=start_date, end=end_date, periods=len(data))
    data['日期'] = dates
    data.set_index('日期', inplace=True)

    # 技术分析
    ma_short = moving_average(data['收盘到期收益率(%)'], window=5)
    ma_long = moving_average(data['收盘到期收益率(%)'], window=20)
    macd_line, signal_line = macd(data['收盘到期收益率(%)'], short_period=12, long_period=26, signal_period=9)
    rsi_indicator = RSIIndicator(close=data['收盘到期收益率(%)'], window=14)
    rsi = rsi_indicator.rsi()

    bb_indicator = BollingerBands(close=data['收盘到期收益率(%)'], window=20, window_dev=2)
    upper_band = bb_indicator.bollinger_hband()
    lower_band = bb_indicator.bollinger_lband()

    # 创建图表1: 收盘到期收益率与移动平均线
    fig1 = go.Figure()
    fig1.add_trace(
        go.Scatter(x=data.index, y=data['收盘到期收益率(%)'], name='收盘到期收益率', line=dict(color='#1f77b4')))
    fig1.add_trace(go.Scatter(x=data.index, y=ma_short, name='5日移动平均线', line=dict(color='#ff7f0e')))
    fig1.add_trace(go.Scatter(x=data.index, y=ma_long, name='20日移动平均线', line=dict(color='#2ca02c')))
    fig1.update_layout(
        xaxis=dict(title='日期', tickformat='%Y-%m-%d', gridcolor='#f0f0f0', showgrid=True),
        yaxis=dict(title='收盘到期收益率(%)', gridcolor='#f0f0f0', showgrid=True),
        plot_bgcolor='#ffffff',
        legend=dict(x=0, y=1, orientation='h', bgcolor='#f0f0f0', bordercolor='#000000', borderwidth=1),
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    fig1.update_xaxes(tickangle=-45, tickfont=dict(size=10), nticks=10)

    # 创建图表2: MACD指标
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=data.index, y=macd_line, name='MACD', line=dict(color='#d62728')))
    fig2.add_trace(go.Scatter(x=data.index, y=signal_line, name='Signal', line=dict(color='#9467bd')))
    fig2.update_layout(
        xaxis=dict(title='日期', tickformat='%Y-%m-%d', gridcolor='#f0f0f0', showgrid=True),
        yaxis=dict(title='MACD', gridcolor='#f0f0f0', showgrid=True),
        plot_bgcolor='#ffffff',
        legend=dict(x=0, y=1, orientation='h', bgcolor='#f0f0f0', bordercolor='#000000', borderwidth=1),
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    fig2.update_xaxes(tickangle=-45, tickfont=dict(size=10), nticks=10)

    # 创建图表3: 相对强弱指数(RSI)
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=data.index, y=rsi, name='RSI', line=dict(color='#9467bd')))
    fig3.add_shape(
        type="line",
        x0=data.index[0],
        y0=30,
        x1=data.index[-1],
        y1=30,
        line=dict(color="#ffa500", width=2, dash="dash"),
    )
    fig3.add_shape(
        type="line",
        x0=data.index[0],
        y0=70,
        x1=data.index[-1],
        y1=70,
        line=dict(color="#ffa500", width=2, dash="dash"),
    )
    fig3.update_layout(
        xaxis=dict(title='日期', tickformat='%Y-%m-%d', gridcolor='#f0f0f0', showgrid=True),
        yaxis=dict(title='RSI', gridcolor='#f0f0f0', showgrid=True),
        plot_bgcolor='#ffffff',
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    fig3.update_xaxes(tickangle=-45, tickfont=dict(size=10), nticks=10)

    # 创建图表4: 布林带
    fig4 = go.Figure()
    fig4.add_trace(
        go.Scatter(x=data.index, y=data['收盘到期收益率(%)'], name='收盘到期收益率', line=dict(color='#1f77b4')))
    fig4.add_trace(
        go.Scatter(x=data.index, y=upper_band, name='上轨', line=dict(color='#ff7f0e', width=1, dash='dash')))
    fig4.add_trace(
        go.Scatter(x=data.index, y=lower_band, name='下轨', line=dict(color='#2ca02c', width=1, dash='dash')))
    fig4.update_layout(
        xaxis=dict(title='日期', tickformat='%Y-%m-%d', gridcolor='#f0f0f0', showgrid=True),
        yaxis=dict(title='收盘到期收益率(%)', gridcolor='#f0f0f0', showgrid=True),
        plot_bgcolor='#ffffff',
        legend=dict(x=0, y=1, orientation='h', bgcolor='#f0f0f0', bordercolor='#000000', borderwidth=1),
        height=400,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    fig4.update_xaxes(tickangle=-45, tickfont=dict(size=10), nticks=10)

    # 将图表转换为HTML
    plot1_html = fig1.to_html(full_html=False)
    plot2_html = fig2.to_html(full_html=False)
    plot3_html = fig3.to_html(full_html=False)
    plot4_html = fig4.to_html(full_html=False)

    return render_template('visualize.html', plot1=plot1_html, plot2=plot2_html, plot3=plot3_html, plot4=plot4_html,
                           stats=stats)
@app.route('/comment')
def comment():
    return render_template('comment.html')

@app.route('/query', methods=['GET', 'POST'])
def query():
    if request.method == 'POST':
        search_term = request.form['search_term'].lower()

        data = load_data()

        # 删除任何没有'债券简称'的行。
        data = data.dropna(subset=['债券简称'])

        # 创建小写版本以进行搜索。
        data['债券简称_lower'] = data['债券简称'].str.lower()

        filtered_data = data[data['债券简称_lower'].str.contains(search_term)]

        print('Filtered data:', filtered_data.to_dict('records'))  # 打印转换后的字典数据

        # 将 NaN 转换为 None，以便正确地序列化为 JSON。
        filtered_data = filtered_data.where(pd.notnull(filtered_data), 0)

        return jsonify(filtered_data.to_dict('records'))

    else:
        data = load_data()

        # 删除任何没有'债券简称'的行。
        data = data.dropna(subset=['债券简称'])

        random_bonds = random.sample(data['债券简称'].tolist(), 5)

        return render_template('query.html', random_bonds=random_bonds)


@app.route('/suggestions')
def suggestions():
    search_term = request.args.get('search_term', '').lower()  # 将搜索词转换为小写
    data = load_data()
    data = data.dropna(subset=['债券简称'])
    suggestions = data['债券简称'].unique()
    filtered_suggestions = [s for s in suggestions if search_term in s.lower()]  # 使用小写进行匹配
    return jsonify(filtered_suggestions[:10])

@app.route('/report')
def report():
    return render_template('report.html')



import random
from datetime import datetime, timedelta

def generate_stock_code():
    return str(random.randint(100000, 999999))


import akshare as ak
from datetime import datetime, timedelta


def generate_kdj_data(stock_code, count):
    # 获取当前日期
    end_date = datetime.now().strftime("%Y%m%d")
    # 计算30个交易日前的日期
    start_date = (datetime.now() - timedelta(days=count)).strftime("%Y%m%d")

    # 调用 akshare 接口获取指定股票代码和日期范围内的历史行情数据
    stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date, end_date=end_date,
                                            adjust="")

    data = []
    for _, row in stock_zh_a_hist_df.iterrows():
        date = row['日期'].strftime("%Y-%m-%d")  # 直接将 datetime.date 转换为字符串格式
        close_price = row['收盘']
        low_price = row['最低']
        high_price = row['最高']

        # 计算 KDJ 指标
        if len(data) > 0:
            last_k, last_d = data[-1]['k'], data[-1]['d']
        else:
            last_k, last_d = 50, 50

        rsv = (close_price - low_price) / (high_price - low_price) * 100 if high_price != low_price else 0
        k = 2 / 3 * last_k + 1 / 3 * rsv
        d = 2 / 3 * last_d + 1 / 3 * k
        j = 3 * k - 2 * d

        data.append({"date": date, "k": round(k, 2), "d": round(d, 2), "j": round(j, 2)})

    return data

def generate_stock_code():
    return str(random.randint(100000, 999999))


@app.route('/api/kdj_data')
def kdj_data():
    stock_code = request.args.get('stock_code', '000001')  # 默认股票代码为 '000001'
    data = generate_kdj_data(stock_code, 100)
    return jsonify(data)

@app.route('/kdj')
def kdj():
    return render_template('kdj.html')

if __name__ == '__main__':
    app.run(debug=True)