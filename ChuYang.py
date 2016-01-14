import re
import requests
from collections import OrderedDict
from lxml import etree
from basespider import BaseSpider

'''
    Spider of 初阳学院新闻 http://cyxy.zjnu.edu.cn/list.aspx?cid=74
'''
__author__ = 'leo'

TABLE_NAME = 'news_chuyang'


class ChuYangSpider(BaseSpider):

    def __init__(self):
        print('Start fetching...')

    def getsource(self, url):
        html = requests.get(url)
        html.encoding = 'gbk' #不确定是是什么编码
        selector = etree.HTML(html.text)
        return selector

    def changepage(self, url, total_page):
        now_page = int(re.findall('page=(\d+)', url, re.S)[0])
        # now_page = int(re.search('page=\d+', url, re.S).group(1)) #page
        page_group = []
        for i in range(now_page, total_page + 1):
            link = re.sub('page=\d+','page=%s' % i, url, re.S)
            page_group.append(link)
        return page_group

    # 提取时间
    def getAllTitlesAndIds(self, selector):
        section = selector.xpath(r'//div[@class="mm"]')[0]
        all_article_dates = section.xpath(r'./div/div/text()')
        all_article_titles = section.xpath(r'./div/a/text()')
        hrefs = section.xpath(r'./div/a/@href')
        # 获取所有的文章id
        all_article_ids = list()
        for each in hrefs:
            id = re.findall(r'id=(\d+)', str(each), re.S)[0]
            all_article_ids.append(id)
        all_articles = list()
        for i in range(0, len(all_article_dates)):
            info = OrderedDict()
            info['articleId'] = str(all_article_ids[i])
            info['date'] = str(all_article_dates[i])
            info['title'] = str(all_article_titles[i])
            all_articles.append(info)
        return all_articles
        # titles = re.findall(r'<div class="dateR gray">(.*?)</div>', selector, re.S)

    def saveinfo(self, classinfo):
        f = open('info.txt', 'a')
        for each in classinfo:
            f.writelines('title:' + each['title'] + '\n')
            f.writelines('articleId:' + each['articleId'] + '\n')
            f.writelines('date:' + each['date'] + '\n')
            f.writelines('\n')
        f.close()

if __name__ == '__main__':

    url = 'http://cyxy.zjnu.edu.cn/list.aspx?cid=74&page=1'
    spider = ChuYangSpider()

    all_links = spider.changepage(url, 2)

    for count, link in enumerate(all_links):
        print('Parsing ' + link + ':')
        selector = spider.getsource(link)
        all_articles = spider.getAllTitlesAndIds(selector)
        for i, each in enumerate(all_articles):
            print('Saving news ' + each['articleId'] + ' to database... ', end='')
            spider.savetodb(TABLE_NAME, each)
            print('Done!')
