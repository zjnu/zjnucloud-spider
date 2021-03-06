import re
import requests
from lxml import etree
from basespider import BaseSpider

'''
    Spider of å­¦æ¯å¨æ?http://news.zjnu.edu.cn/
'''
__author__ = 'ddMax'

TABLE_NAME = 'news_xsdt'


class XSDTSpider(BaseSpider):

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

    # ç±äºæ é¢, IDä¸æ¯ä¸åæ°é»ä¿¡æ¯çç¹å¾ä¸ææ¾ï¼å æ­¤åç¬æåæææ°é»æ é¢?    def getalltitlesandids(self, source):
        titles = re.findall(r'<SPAN style="FONT-WEIGHT:.*?_blank>(.*?)</a>', source, re.S)
        for count, each in enumerate(titles):
            titles[count] = each.strip()
        article_ids = re.findall(r'<SPAN style="FONT-WEIGHT:.*?article_id=(\d*)"', source, re.S)
        # ä»¥ååºçæ¹å¼è¿ååè¡?        return titles[::-1], article_ids[::-1]

    # æåæ¯åæ°é»ä¿¡æ¯ï¼é¤æ é¢åIDï¼?    def getallsection(self, source):
        allsection = re.findall(r'<td bgcolor=FloralWhite>(.*?)</table></td>', source, re.S)
        # ä»¥ååºçæ¹å¼è¿ååè¡?        return allsection[::-1]

    # å¤çæ é¢+æ°é»ä¿¡æ¯ï¼æ´åå°å­å¸ä¸?    def getinfo(self, eachsection, title, articleId):
        info = dict()
        info['title'] = title
        info['articleId'] = int(articleId)
        # info['overview'] = re.search(r'<div class="article_show" align="left">\s*(.*?)</div>', eachsection, re.I).group(1).strip()
        info['overview'] = self.patchstr(str(etree.HTML(eachsection).xpath(r'//tr[2]/td/div/text()')[0]).strip())
        date_author_hits = str(re.findall(r'COLOR: #006600; ">(.*?)</span>', eachsection, re.S))
        info['date'] = re.search(r'----(.*?)&nbsp;', date_author_hits, re.S).group(1).strip()
        info['author'] = re.search(r'ä¾ç¨¿ï¼?.*?)&nbsp;', date_author_hits, re.S).group(1).strip()
        info['hits'] = re.search(r'æµè§æ¬¡æ°ï¼?\d*)', date_author_hits, re.S).group(1).strip()
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

    url = 'http://www.zjnu.edu.cn/news/common/article_list.aspx?border_id=2&pageindex=1'
    spider = XSDTSpider()

    # all_links = spider.changepage(url, 396)
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
