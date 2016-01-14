import requests
import re
from basespider import BaseSpider
from lxml import etree

'''
    Spider of 讲座预告详情
'''
__author__ = 'ddMax'

TABLE_NAME = 'speech_detail'
KEYWORDS = {
    '讲座',
    '浙师资讯',
    '学术活动',
}


class SpeechDetailSpider(BaseSpider):

    def __init__(self):
        print('Start fetching...')

    def getsource(self, url):
        html = requests.get(url)
        return html.text

    def getselector(self, source):
        selector = etree.HTML(self.getsource(source))
        return selector

    def changepage(self, url, total_page):
        now_page = int(re.search('page=(\d+)', url, re.S).group(1))
        page_group = []
        for i in range(now_page, total_page + 1):
            link = re.sub('page=\d+', 'page=%s' % i, url, re.S)
            page_group.append(link)
        return page_group

    def getalldetailids(self, selector):
        all_sections = selector.xpath('//div[@class="title"]')
        result = list()
        for each in all_sections:
            title = str(each.xpath('./a/text()')[0])
            for keyword in KEYWORDS:
                if title.find(keyword) != -1:
                    id = int(re.findall(r'\d+', str(each.xpath('./a/@href')[0]), re.S)[0])
                    result.append(id)
        return result

    def getinfo(self, source, id):
        info = dict()
        info['id'] = id
        # 主体部分，使用正则处理
        restr = r'(<div id="article-inner">\s*).*?(<div class="page-content.*?)<div class="inner-box"'
        match = re.findall(restr, source, re.S)
        article_fragment = match[0]
        article_content = ''
        for i in range(len(article_fragment)):
            article_content += article_fragment[i]
        # 处理特殊内容
        article_content = self.dealcontent(article_content)
        info['content'] = self.patchstr(article_content)
        # 标题、日期，使用XPath处理
        selector = etree.HTML(source)
        title = str(selector.xpath('//h1[@class="title"]/text()')[0])
        title = re.findall(r'(\w.*)', title, re.S)[0]
        info['title'] = title
        info['date'] = str(selector.xpath('//p[@class="bizinfo"]/span/span/text()')[0])
        # title = article_inner.xpath('./div[@class="header"]/h1/text()')
        return info

    def dealcontent(self, content):
        img_tag_groups = re.findall(r'(<img.*?>)', content, re.S)

        # 替换最后的微信公众号图片
        last = len(img_tag_groups)
        kill_logo_str = img_tag_groups[last - 1]
        content = content.replace(kill_logo_str, '')
        # 替换<img>标签中的original为src
        for each in img_tag_groups:
            new = each.replace('original', 'src')
            content = content.replace(each, new)
        return content

    # Escape sequences \" and \'
    def patchstr(self, s):
        if s.find('"') != -1:
            s = s.replace(r'"', r'\"')
        if s.find("'") != -1:
            s = s.replace(r"'", r"\'")
        return s


if __name__ == '__main__':

    url = 'http://www.aiweibang.com/u/25720?page=1'
    url_detail_base = 'http://www.aiweibang.com/yuedu/'
    spider = SpeechDetailSpider()

    # all_links = spider.changepage(url, 1)
    all_links = spider.changepage(url, 2)

    # Deal with each page of news
    for count, link in enumerate(all_links):
        print('Parsing news detail at page ' + str(count + 1) + '...')
        selector = spider.getselector(link)
        all_detail_ids = spider.getalldetailids(selector)
        for i, detail_id in enumerate(all_detail_ids):
            # 拼接最终详情url地址
            url_detail = url_detail_base + str(detail_id) + ".html"  # That's the final link
            # etree对象
            selector_detail = spider.getsource(url_detail)
            # 详情结果字典
            info = spider.getinfo(selector_detail, detail_id)
            print('-->Saving detail of news ' + str(detail_id) + ' to database... ', end='')
            spider.savetodb(TABLE_NAME, info)
            print("Done!")
