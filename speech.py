import requests
import re
from basespider import BaseSpider
from lxml import etree
from datetime import datetime

'''
    Spider of 讲座预告 http://www.aiweibang.com/u/25720
'''
__author__ = 'ddMax'

TABLE_NAME = 'speech'


class SpeechSpider(BaseSpider):

    def __init__(self):
        print('Start fetching...')

    def getsource(self, url):
        html = requests.get(url)
        selector = etree.HTML(html.text)
        return selector

    def changepage(self, url, total_page):
        now_page = int(re.search('page=(\d+)', url, re.S).group(1))
        page_group = []
        for i in range(now_page, total_page + 1):
            link = re.sub('page=\d+', 'page=%s' % i, url, re.S)
            page_group.append(link)
        return page_group

    # 提取所有的讲座信息div块
    def getallsection(self, selector):
        allsection = selector.xpath('//div[@class="msg-item"]')
        # 检测包含讲座关键字的新闻，并返回
        target = list()
        for each in allsection:
            title = str(each.xpath('./div[@class="info"]/div[@class="title"]/a/text()')[0])
            if title.find('讲座') != -1 and title.find('浙师资讯') != -1:
                target.append(each)
        return target

    # 处理每条讲座信息，整合到字典中
    def getinfo(self, each):
        info = dict()
        date_day = str(each.xpath('./div[@class="date"]/span[@class="day"]/text()')[0])
        date_month = str(each.xpath('./div[@class="date"]/span[@class="month"]/text()')[0])
        date = datetime.strptime(date_month + '-' + date_day, '%y-%m-%d').strftime('%Y-%m-%d')
        info['date'] = date
        each_info = each.xpath('./div[@class="info"]')[0]
        info['title'] = str(each_info.xpath('./div[@class="title"]/a/text()')[0])
        href = str(each_info.xpath('./div[@class="title"]/a/@href')[0])
        info['href'] = 'http://www.aiweibang.com' + href
        info['id'] = int(re.findall(r'\d+', href, re.S)[0])
        each_info_summary = each_info.xpath('./div[@class="summary"]')[0]
        info['pic'] = str(each_info_summary.xpath('./div[@class="pic"]/div[@class="picinner"]/a/img/@original')[0])
        overview = str(each_info_summary.xpath('./div[@class="text"]/text()'))
        overview = re.findall(r'[^\'\[\]\\]+', overview, re.I)[0]
        info['overview'] = self.patchstr(overview)
        return info

if __name__ == '__main__':

    url = 'http://www.aiweibang.com/u/25720?page=1'
    spider = SpeechSpider()

    # all_links = spider.changepage(url, 12)
    all_links = spider.changepage(url, 1)

    for count, link in enumerate(all_links):
        print('Parsing ' + link + ':')
        html = spider.getsource(link)
        all_sections = spider.getallsection(html)

        for i, each in enumerate(all_sections):
            info = spider.getinfo(each)
            print('Saving news ' + info.get('title') + ' to database... ', end='')
            spider.savetodb(TABLE_NAME, info)
            print('Done!')


