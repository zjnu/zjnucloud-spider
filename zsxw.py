import requests
import re
from basespider import BaseSpider
from lxml import etree

'''
    Spider of 浙师新闻 http://news.zjnu.edu.cn/
'''
__author__ = 'ddMax'

TABLE_NAME = 'news_zsxw'


class ZSXWSpider(BaseSpider):

    def __init__(self):
        print('Start fetching...')

    def getsource(self, url):
        html = requests.get(url)
        html.encoding = 'gbk'
        return html.text

    def changepage(self, url, total_page):
        now_page = int(re.search('pageindex=(\d+)', url, re.S).group(1))
        page_group = []
        for i in range(now_page, total_page + 1):
            link = re.sub('pageindex=\d+', 'pageindex=%s' % i, url, re.S)
            page_group.append(link)
        return page_group

    # 由于标题, ID与每一块新闻信息的特征不明显，因此单独抓取所有新闻标�?    def getalltitlesandids(self, source):
        titles = re.findall(r'<SPAN style="FONT-WEIGHT:.*?_blank>(.*?)</a>', source, re.S)
        for count, each in enumerate(titles):
            titles[count] = each.strip()
        article_ids = re.findall(r'<SPAN style="FONT-WEIGHT:.*?article_id=(\d*)"', source, re.S)
        # 以倒序的方式返回列�?        return titles[::-1], article_ids[::-1]

    # 提取每块新闻信息（除标题和ID�?    def getallsection(self, source):
        allsection = re.findall(r'<td bgcolor=FloralWhite>(.*?)</table></td>', source, re.S)
        # 以倒序的方式返回列�?        return allsection[::-1]

    # 处理标题+新闻信息，整合到字典�?    def getinfo(self, eachsection, title, articleId):
        info = dict()
        info['title'] = title
        info['articleId'] = int(articleId)
        # info['overview'] = re.search(r'<div class="article_show" align="left">\s*(.*?)</div>', eachsection, re.I).group(1).strip()
        info['overview'] = self.patchstr(str(etree.HTML(eachsection).xpath(r'//tr[2]/td/div/text()')[0]).strip())
        date_author_hits = str(re.findall(r'COLOR: #006600; ">(.*?)</span>', eachsection, re.S))
        info['date'] = re.search(r'----(.*?)&nbsp;', date_author_hits, re.S).group(1).strip()
        info['author'] = re.search(r'供稿�?.*?)&nbsp;', date_author_hits, re.S).group(1).strip()
        info['hits'] = re.search(r'浏览次数�?\d*)', date_author_hits, re.S).group(1).strip()
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

if __name__ == '__main__':

    # classinfo = []
    url = 'http://www.zjnu.edu.cn/news/common/article_list.aspx?border_id=1&pageindex=1'
    spider = ZSXWSpider()

    # all_links = spider.changepage(url, 318)
    all_links = spider.changepage(url, 4)

    for count, link in enumerate(all_links):
        print('Parsing ' + link + ':')
        html = spider.getsource(link)
        all_titles, all_article_ids = spider.getalltitlesandids(html)
        all_sections = spider.getallsection(html)

        for i, each in enumerate(all_sections):
            info = spider.getinfo(each, all_titles[i], all_article_ids[i])
            print('Saving news ' + all_article_ids[i] + ' to database... ', end='')
            spider.savetodb(TABLE_NAME, info)
            print('Done!')
            # classinfo.append(info)

    # spider.saveinfo(classinfo)
