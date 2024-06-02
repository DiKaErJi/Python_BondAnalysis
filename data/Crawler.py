# -*- coding: utf-8 -*-

# 在所有导入之前调用 monkey.patch_all()
import gevent
from gevent import monkey, pool
monkey.patch_all()  # 打补丁，使标准库中的阻塞操作变为非阻塞

import time  # 导入time模块，用于延时和时间处理
import re  # 导入re模块，用于正则表达式操作
import requests  # 导入requests库，用于发送HTTP请求
from concurrent import futures  # 导入futures模块，用于并发执行
from bs4 import BeautifulSoup  # 导入BeautifulSoup库，用于解析HTML和XML文档
from pymongo import MongoClient  # 导入MongoClient，用于连接MongoDB数据库
import Text_Analysis.text_mining as tm  # 导入自定义的文本分析模块


class WebCrawlFromcnstock(object):
    '''从以下网址抓取公司新闻：
        'http://company.cnstock.com/company/scp_gsxw/1',
        'http://ggjd.cnstock.com/gglist/search/qmtbbdj/1',
        'http://ggjd.cnstock.com/gglist/search/ggkx/1'。
    参数:
        totalPages: 设置要抓取的总页数。
        Range: 将总网页数分成totalPages/Range部分进行多线程处理。
        ThreadsNum: 需要启动的线程数量。
        dbName: 数据库名称。
        colName: 集合名称。
        IP: 本地IP地址。
        PORT: 对应IP地址的端口号。
    '''

    def __init__(self, **kwarg):
        # 初始化函数，接收多个关键字参数
        self.ThreadsNum = kwarg['ThreadsNum']  # 线程数量
        self.dbName = kwarg['dbName']  # 数据库名称
        self.colName = kwarg['collectionName']  # 集合名称
        self.IP = kwarg['IP']  # IP地址
        self.PORT = kwarg['PORT']  # 端口号
        self.Prob = .5  # 中文文本的阈值概率
        self.realtimeNewsURL = []  # 实时新闻URL列表
        self.tm = tm.TextMining(IP="localhost", PORT=27017)  # 初始化文本挖掘对象

    def ConnDB(self):
        '''连接MongoDB数据库。
        '''
        Conn = MongoClient(self.IP, self.PORT)  # 连接到MongoDB
        db = Conn[self.dbName]  # 选择数据库
        self._collection = db.get_collection(self.colName)  # 获取集合

    def countchn(self, string):
        '''统计中文字符数量并计算中文出现的频率。
        参数:
            string: 通过BeautifulSoup分析的网页部分。
        '''
        pattern = re.compile(u'[\u1100-\uFFFDh]+?')  # 编译正则表达式，匹配中文字符
        result = pattern.findall(string)  # 查找所有匹配的中文字符
        chnnum = len(result)  # 中文字符数量
        possible = chnnum / len(str(string))  # 中文字符占总字符的比例
        return (chnnum, possible)  # 返回中文字符数量和比例

    def getUrlInfo(self, url):
        '''分析网页并提取有用信息。
        '''
        respond = requests.get(url)  # 发送HTTP GET请求
        respond.encoding = BeautifulSoup(respond.content, "lxml").original_encoding  # 设置响应的编码
        bs = BeautifulSoup(respond.text, "lxml")  # 解析HTML文档
        span_list = bs.find_all('span')  # 查找所有的span标签
        part = bs.find_all('p')  # 查找所有的p标签
        article = ''  # 初始化文章内容
        date = ''  # 初始化日期

        for span in span_list:
            if 'class' in span.attrs and span['class'] == ['timer']:  # 查找包含时间信息的span标签
                date = span.text  # 提取时间
                break

        for paragraph in part:
            chnstatus = self.countchn(str(paragraph))  # 统计中文字符
            possible = chnstatus[1]  # 获取中文字符比例
            if possible > self.Prob:  # 如果中文字符比例大于阈值
                article += str(paragraph)  # 添加到文章内容中

        while article.find('<') != -1 and article.find('>') != -1:  # 去除文章中的HTML标签
            string = article[article.find('<'):article.find('>')+1]
            article = article.replace(string, '')

        while article.find('\u3000') != -1:  # 去除中文全角空格
            article = article.replace('\u3000', '')

        article = ' '.join(re.split(' +|\n+', article)).strip()  # 去除多余的空格和换行符

        return date, article  # 返回日期和文章内容

    def GenPagesLst(self, totalPages, Range, initPageID):
        '''使用Range参数生成页码列表。
        '''
        PageLst = []  # 初始化页码列表
        k = initPageID  # 初始页码
        while k + Range - 1 <= totalPages:
            PageLst.append((k, k + Range - 1))  # 将页码范围添加到列表
            k += Range  # 更新页码
        if k + Range - 1 < totalPages:
            PageLst.append((k, totalPages))  # 添加剩余的页码范围
        return PageLst  # 返回页码列表

    def CrawlHistoryCompanyNews(self, startPage, endPage, url_Part_1):
        '''抓取历史公司新闻。
        '''
        self.ConnDB()  # 连接数据库
        AddressLst = self.extractData(['Address'])[0]  # 提取地址列表
        if AddressLst == []:
            urls = []
            for pageId in range(startPage, endPage + 1):
                urls.append(url_Part_1 + str(pageId))  # 构建URL列表
            for url in urls:
                print(url)
                resp = requests.get(url)  # 发送HTTP GET请求
                resp.encoding = BeautifulSoup(resp.content, "lxml").original_encoding  # 设置响应的编码
                bs = BeautifulSoup(resp.text, "lxml")  # 解析HTML文档
                a_list = bs.find_all('a')  # 查找所有的a标签
                for a in a_list:
                    if ('href' in a.attrs and 'target' in a.attrs and 'title' in a.attrs
                        and a['href'].find('http://company.cnstock.com/company/') != -1
                        and a.parent.find('span')):  # 检查a标签的属性
                        date, article = self.getUrlInfo(a['href'])  # 获取文章信息
                        while article == '' and self.Prob >= .1:
                            self.Prob -= .193  # 调整阈值
                            date, article = self.getUrlInfo(a['href'])
                        self.Prob = .5  # 重置阈值
                        if article != '':
                            data = {'Date': date, 'Address': a['href'], 'Title': a['title'], 'Article': article}
                            self._collection.insert_one(data)  # 插入数据库
        else:
            urls = []
            for pageId in range(startPage, endPage + 1):
                urls.append(url_Part_1 + str(pageId))  # 构建URL列表
            for url in urls:
                print(' <Re-Crawl url> ', url)
                resp = requests.get(url)  # 发送HTTP GET请求
                resp.encoding = BeautifulSoup(resp.content, "lxml").original_encoding  # 设置响应的编码
                bs = BeautifulSoup(resp.text, "lxml")  # 解析HTML文档
                a_list = bs.find_all('a')  # 查找所有的a标签
                for a in a_list:
                    if ('href' in a.attrs and 'target' in a.attrs and 'title' in a.attrs
                        and a['href'].find('http://company.cnstock.com/company/') != -1
                        and a.parent.find('span')):  # 检查a标签的属性
                        if a['href'] not in AddressLst:
                            date, article = self.getUrlInfo(a['href'])  # 获取文章信息
                            while article == '' and self.Prob >= .1:
                                self.Prob -= .1  # 调整阈值
                                date, article = self.getUrlInfo(a['href'])
                            self.Prob = .5  # 重置阈值
                            if article != '':
                                data = {'Date': date, 'Address': a['href'], 'Title': a['title'], 'Article': article}
                                self._collection.insert_one(data)  # 插入数据库

    def CrawlRealtimeCompanyNews(self, url_part_lst):
        '''继续抓取公司新闻，并每隔一段时间提取有用信息，
           包括摘要、关键字、发布时间、相关股票代码列表和主要内容。
        '''
        doc_lst = []
        self.ConnDB()  # 连接数据库
        self._AddressLst = self.extractData(['Address'])[0]  # 提取地址列表
        for url_Part in url_part_lst:
            url = url_Part + str(1)
            resp = requests.get(url)  # 发送HTTP GET请求
            resp.encoding = BeautifulSoup(resp.content, "lxml").original_encoding  # 设置响应的编码
            bs = BeautifulSoup(resp.text, "lxml")  # 解析HTML文档
            a_list = bs.find_all('a')  # 查找所有的a标签
            if len(self.realtimeNewsURL) == 0:
                for a in a_list:
                    if (('href' in a.attrs and 'target' in a.attrs and 'title' in a.attrs
                         and a['href'].find('http://company.cnstock.com/company/') != -1
                         and a.parent.find('span')) or
                        ('href' in a.attrs and 'target' in a.attrs and 'title' in a.attrs
                         and a['href'].find('http://ggjd.cnstock.com/company/') != -1
                         and a.parent.find('span'))):  # 检查a标签的属性
                        if a['href'] not in self._AddressLst:
                            self.realtimeNewsURL.append(a['href'])  # 添加到实时新闻URL列表
                            date, article = self.getUrlInfo(a['href'])  # 获取文章信息
                            while article == '' and self.Prob >= .1:
                                self.Prob -= .1  # 调整阈值
                                date, article = self.getUrlInfo(a['href'])
                            self.Prob = .5  # 重置阈值
                            if article != '':
                                data = {'Date': date, 'Address': a['href'], 'Title': a['title'], 'Article': article}
                                self._collection.insert_one(data)  # 插入数据库
                                doc_lst.append(a['title'] + ' ' + article)
                                print(' [' + date + '] ' + a['title'])
            else:
                for a in a_list:
                    if (('href' in a.attrs and 'target' in a.attrs and 'title' in a.attrs
                         and a['href'].find('http://company.cnstock.com/company/') != -1
                         and a.parent.find('span')) or
                        ('href' in a.attrs and 'target' in a.attrs and 'title' in a.attrs
                         and a['href'].find('http://ggjd.cnstock.com/company/') != -1
                         and a.parent.find('span'))):  # 检查a标签的属性
                        if a['href'] not in self.realtimeNewsURL and a['href'] not in self._AddressLst:
                            self.realtimeNewsURL.append(a['href'])  # 添加到实时新闻URL列表
                            date, article = self.getUrlInfo(a['href'])  # 获取文章信息
                            while article == '' and self.Prob >= .1:
                                self.Prob -= .1  # 调整阈值
                                date, article = self.getUrlInfo(a['href'])
                            self.Prob = .5  # 重置阈值
                            if article != '':
                                data = {'Date': date, 'Address': a['href'], 'Title': a['title'], 'Article': article}
                                self._collection.insert_one(data)  # 插入数据库
                                doc_lst.append(a['title'] + ' ' + article)
                                print(' [' + date + '] ' + a['title'])
        return doc_lst

    def extractData(self, tag_list):
        '''从集合中提取包含在'tag_list'中的列数据到列表中。
        '''
        data = []
        for tag in tag_list:
            exec(tag + " = self._collection.distinct('" + tag + "')")  # 提取集合中指定字段的所有唯一值
            exec("data.append(" + tag + ")")  # 将提取的数据添加到列表中
        return data

    def coroutine_run(self, totalPages, Range, initPageID, **kwarg):
        '''协程运行。
        '''
        jobs = []
        page_ranges_lst = self.GenPagesLst(totalPages, Range, initPageID)  # 生成页码范围列表
        for page_range in page_ranges_lst:
            jobs.append(gevent.spawn(self.CrawlHistoryCompanyNews, page_range[0], page_range[1], kwarg['url_Part_1']))  # 创建协程任务
        gevent.joinall(jobs)  # 启动协程

    def multi_threads_run(self, **kwarg):
        '''多线程运行。
        '''
        page_ranges_lst = self.GenPagesLst()  # 生成页码范围列表
        print(' 使用 ' + str(self.ThreadsNum) + ' 个线程收集新闻 ... ')
        with futures.ThreadPoolExecutor(max_workers=self.ThreadsNum) as executor:  # 创建线程池
            future_to_url = {executor.submit(self.CrawlHistoryCompanyNews, page_range[0], page_range[1]): \
                             ind for ind, page_range in enumerate(page_ranges_lst)}  # 提交任务到线程池

    def classifyRealtimeStockNews(self):
        '''每隔60秒持续抓取并分类新闻（文章/文档）。
        '''
        while True:
            print(' * 开始从CNSTOCK抓取新闻 ... ')
            doc_list = self.CrawlRealtimeCompanyNews(['http://company.cnstock.com/company/scp_gsxw/',\
                                                    'http://ggjd.cnstock.com/gglist/search/qmtbbdj/',\
                                                    'http://ggjd.cnstock.com/gglist/search/ggkx/'])  # 抓取实时公司新闻
            print(' * 完成抓取 ... ')
            if len(doc_list) != 0:
                self.tm.classifyRealtimeStockNews(doc_list)  # 分类实时股票新闻
            time.sleep(60)  # 每隔60秒重新抓取一次
