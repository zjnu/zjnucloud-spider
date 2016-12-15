import re
import requests
import time
from datetime import datetime
from lxml import etree
from basespider import BaseSpider

'''
    Spider of news detail on 浙师新闻
'''
__author__ = 'ddMax'

TABLE_NAME = 'news_zsxw_detail'


class ZSXWDetailSpider(BaseSpider):

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
            info['videolink'] = re.search(r'addVariable\("link","(.*?)"\);', content, re.S).group(1).strip()
            videocover = 'http://www.zjnu.edu.cn'
            videocover += re.search(r'addVariable\("image","(.*?)"\);', content, re.S).group(1).strip()
            info['videocover'] = videocover
            videopart = re.search(r'(<div id="player.*</div>)', content, re.S).group(1).strip()
            content = content.replace(videopart, '')
        else:
            info['videolink'] = ''
            info['videocover'] = ''
        # Escaping characters
        content = self.patchstr(content)
        return content

    def getinfo(self, resource):
        info = dict()
        # Use XPath to deal with title, date, author, deptname
        selector = etree.HTML(resource)
        info['title'] = self.patchstr(str(selector.xpath(r'//*[@id="mytitle"]/text()')[0]))
        date = datetime.strptime(str(selector.xpath(r'//*[@id="mydate"]/text()')[0]), '%Y-%m-%d')
        # info['date'] = date.strftime('%Y-%m-%d')
        info['date'] = date.strftime('%Y年%m月%d日')
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

if __name__ == '__main__':

    url = 'http://www.zjnu.edu.cn/news/common/article_list.aspx?border_id=1&pageindex=1'
    url_detail = 'http://www.zjnu.edu.cn/news/common/article_show.aspx?article_id='
    spider = ZSXWDetailSpider()

    # all_links = spider.changepage(url, 318)
    all_links = spider.changepage(url, 4)

    # Deal with each page of news
    for count, link in enumerate(all_links):
        print('Parsing news detail at page ' + str(count + 1) + '...')
        all_detail_ids = re.findall(r'style="FONT-WEIGHT.*?article_id=(\d+)', spider.getresource(link), re.S)
        for i, detail_id in enumerate(all_detail_ids):
            link_detail = url_detail + detail_id  # That's the final link

            resource = spider.getresource(link_detail)
            info = spider.getinfo(resource)
            print('-->Saving detail of news ' + str(detail_id) + ' to database... ', end='')
            spider.savetodb(TABLE_NAME, info)
            print("Done!")
        if count > 10 and count % 10 == 1:
            print('Sleep 20 secs...')
            time.sleep(20)
