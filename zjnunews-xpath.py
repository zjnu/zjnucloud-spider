# -*- coding: utf-8 -*-

import requests
import mysql.connector
import re
from lxml import etree

'''
    Spider of http://news.zjnu.edu.cn/
'''
__author__ = 'ddMax'
TABLE_NAME = 'news_zsxw'


class ZJNUNewsSpider(object):

    def __init__(self):
        print('Start fetching...')

    def getsource(self, url):
        html = requests.get(url)
        html.encoding = 'gbk'
        selector = etree.HTML(html.text)
        return selector

    def changepage(self, url, total_page):
        now_page = int(re.search('pageindex=(\d+)', url, re.S).group(1))
        page_group = []
        for i in range(now_page, total_page + 1):
            link = re.sub('pageindex=\d+', 'pageindex=%s' % i, url, re.S)
            page_group.append(link)
        return page_group

    # 提取所有新闻标题
    def getalltitlesandids(self, source):
        all_titles = source.xpath(r'//*[@style="FONT-WEIGHT: normal; FONT-SIZE: 13px; LINE-HEIGHT: normal; '
                                  r'FONT-STYLE: normal; FONT-VARIANT: normal"]/strong/a/text()')
        all_article_ids = source.xpath
        for count, each in enumerate(all_titles):
            all_titles[count] = each.strip()
        return all_titles

    # 提取每块新闻信息（除标题）
    def getallsection(self, source):
        all_sections = source.xpath(r'//*[@bgcolor="FloralWhite"]/table')
        return all_sections

    # 处理标题+新闻信息，整合到字典中
    def getinfo(self, each_section, title):
        info = dict()
        info['title'] = title
        info['articleId'] = each_section.xpath(r'//tbody/tr[2]/td/div')
        info['overview'] = re.search(r'<div class="article_show" align="left">\s*(.*?)</div>', each_section, re.I).group(1).strip()
        date_author_hits = str(re.findall(r'COLOR: #006600; ">(.*?)</span>', each_section, re.S))
        info['date'] = re.search(r'----(.*?)&nbsp;', date_author_hits, re.S).group(1).strip()
        info['author'] = re.search(r'供稿：(.*?)&nbsp;', date_author_hits, re.S).group(1).strip()
        info['hits'] = re.search(r'浏览次数：(\d*)', date_author_hits, re.S).group(1).strip()
        return info

    def saveinfo(self, classinfo):
        f = open('info.txt', 'a')
        for each in classinfo:
            f.writelines('title:' + each['title'] + '\n')
            f.writelines('articleId:' + each['articleId'] + '\n')
            f.writelines('overview:' + each['overview'] + '\n')
            f.writelines('date:' + each['date'] + '\n')
            f.writelines('author:' + each['author'] + '\n')
            f.writelines('hits:' + each['hits'] + '\n')
            f.writelines('\n')
        f.close()

    def savetodb(self, table_name, dicdata):
        conn = mysql.connector.connect(host='45.124.65.169', user='root', password='{ddmax}', database='zjnucloud')
        cursor = conn.cursor()

        # Convert dict into column->value
        column = ''
        row = ''
        for key in dicdata.keys():
            try:
                column = column + ' ' + key + ','
                if key == 'articleId':
                    # 坑！
                    # row = (row + '%d' + ',') % (dicdata[key])
                    row += '{},'.format(dicdata[key])
                else:
                    # 坑！
                    # row = (row + '"%s"' + ',') % (dicdata[key])
                    row += '"{}",'.format(dicdata[key])
            except ValueError as e:
                print('错误：{}'.format(e))

        # Insert a row of news
        try:
            cursor.execute('INSERT IGNORE INTO %s(%s) VALUES (%s)' % (table_name, column[:-1], row[:-1]))
        except mysql.connector.Error as e:
            print('Error: {}'.format(e))
        conn.commit()
        cursor.close()
        conn.close()

if __name__ == '__main__':

    classinfo = []
    url = 'http://www.zjnu.edu.cn/news/common/article_list.aspx?border_id=1&pageindex=252'
    spider = ZJNUNewsSpider()

    all_links = spider.changepage(url, 313)

    for count, link in enumerate(all_links):
        print('Parsing ' + link + ':')
        selector = spider.getsource(link)
        all_titles = spider.getalltitlesandids(selector)
        all_sections = spider.getallsection(selector)

        for i, each in enumerate(all_sections):
            info = spider.getinfo(each, all_titles[i])
            # print('Saving news ' + all_article_ids[i] + ' to database ...', end='')
            # spider.savetodb(TABLE_NAME, info)
            # print('Done!')
            # classinfo.append(info)

    # spider.saveinfo(classinfo)
