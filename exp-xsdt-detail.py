import requests
import re
from datetime import datetime
from basespider import BaseSpider
from lxml import etree
from multiprocessing.dummy import Pool
import time

'''
    Spider of news detail on 学术动态
'''
__author__ = 'ddMax'

TABLE_NAME = 'news_xsdt_detail'
pool = Pool(8)


class XSDTDetailSpider(BaseSpider):

    def __init__(self):
        print('Start fetching...')

    def getresource(self, url):
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

    # Deal with some complicated situation in some contents
    def dealcontent(self, info, content):
        content = content.replace('src="/zjnu', 'src="http://www.zjnu.edu.cn/zjnu')
        # Contains video
        if content.find('swfobject.js') != -1:
            info['videolink'] = re.search(r'url=(.*?)\s+iurl', content, re.S).group(1).strip()
            videopart = re.search(r'(<div id="player.*</div>)', content, re.S).group(1).strip()
            content = content.replace(videopart, '')
        else:
            info['videolink'] = ''
        # Escaping characters
        content = self.patchstr(content)
        return content

    def getinfo(self, resource):
        info = dict()
        # Use XPath to deal with title, date, author, deptname
        selector = etree.HTML(resource)
        info['title'] = self.patchstr(str(selector.xpath(r'//*[@id="mytitle"]/text()')[0]))
        date = datetime.strptime(str(selector.xpath(r'//*[@id="mydate"]/text()')[0]), '%Y-%m-%d')
        info['date'] = date.strftime('%Y.%m.%d')
        # Find the case that author can be blank!
        author = selector.xpath(r'//*[@id="myauthor"]/text()')
        info['author'] = str(author[0] if len(author) != 0 else '')
        info['deptname'] = str(selector.xpath(r'//*[@id="mydeptname"]/text()')[0])
        # Use regex to deal with articleId, content of news
        info['articleId'] = int(re.search(r'action.*?article_id=(\d+)', resource, re.S).group(1).strip())
        content = re.search(r'id="mycontent">(.*?)</span>', resource, re.S).group(1).strip()
        # Deal with content of news
        info['content'] = self.dealcontent(info, content)
        return info

    # Escape sequences \" and \'
    def patchstr(self, s):
        if s.find('"') != -1:
            s = s.replace(r'"', r'\"')
        if s.find("'") != -1:
            s = s.replace(r"'", r"\'")
        return s


if __name__ == '__main__':

    url = 'http://www.zjnu.edu.cn/news/common/article_list.aspx?border_id=2&pageindex=1'
    url_detail = 'http://www.zjnu.edu.cn/news/common/article_show.aspx?article_id='
    spider = XSDTDetailSpider()

    all_links = spider.changepage(url, 10)

    # Fetch all_links_contents from all_links using multiprocessing
    time1 = time.time()
    all_links_contents = pool.map(spider.getresource, all_links)
    # pool.close()
    # pool.join()
    time2 = time.time()
    print('Fetch all_links_contents time elapsed：' + str(time2-time1))

    # Get all news detail pages links:
    all_detail_links = []
    for count, content in enumerate(all_links_contents):
        print('Parsing news detail at page ' + str(count + 1) + '...')
        all_detail_ids = re.findall(r'style="FONT-WEIGHT.*?article_id=(\d+)', content, re.S)
        for i, detail_id in enumerate(all_detail_ids):
            all_detail_links.append(url_detail + detail_id)  # That's the final link

    # Fetch all_detail_contents from all_detail_links using multiprocessing
    time1 = time.time()
    all_detail_contents = pool.map(spider.getresource, all_detail_links)
    time2 = time.time()
    print('Fetch all_detail_contents time elapsed：' + str(time2-time1))

    # Deal with each detail content
    print('Saving details of news to database... ', end='')
    time1 = time.time()
    for each in all_detail_contents:
        info = spider.getinfo(each)
        spider.savetodb(TABLE_NAME, info)
    time2 = time.time()
    print("Done!")
    print("Saving time elapsed: " + str(time2-time1))

    # Close pool
    pool.close()
    pool.join()
