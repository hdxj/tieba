# -*- coding: utf-8 -*-
import scrapy
import time
import re
import mysql.connector
from tieba import settings


class Dota2Spider(scrapy.Spider):
    name = "dota2"
    is_next_page = True
    allowed_domains = ["tieba.baidu.com"]
    start_urls = ['https://tieba.baidu.com/f?kw={kw}&ie=utf-8&pn=0'.format(kw=settings.kw)]

    def parse(self, response):
        yield scrapy.Request(response.url,callback=self.parse_page)

    def parse_list(self,response):
        list_com = response.xpath('//ul[@id="thread_list"]/li[@class=" j_thread_list clearfix"]')
        page_list = []

        for li in list_com:
            title = li.xpath('.//a[@class="j_th_tit "]/text()').extract_first()
            rep_num = li.xpath('.//span[@class="threadlist_rep_num center_text"]/text()').extract_first()
            dateline = li.xpath('.//span[@class="threadlist_reply_date pull_right j_reply_data"]/text()').extract_first().strip()
            url = 'https://tieba.baidu.com'+li.xpath('.//a[@class="j_th_tit "]/@href').extract_first()
            page_list.append({'title':title,'rep_num':rep_num,'dateline':dateline,'url':url})

        return page_list

    def parse_expired(self,page_list):
        list_is_expired = []
        for page in page_list:
            if ':' in page.get('dateline'):
                list_is_expired.append(page)
            elif '-' in page.get('dateline'):
                dateline = '2018-'+page.get('dateline')
                date = int(time.mktime(time.strptime(dateline, "%Y-%m-%d")))
                now = int(time.time())
                if now - settings.exp_time*86400 < date:
                    list_is_expired.append(page)

        if list_is_expired == []:   #所有帖子时间都过期之后不再翻页
            self.is_next_page = False
        return list_is_expired


    def parse_page(self,response):
        page_list = self.parse_list(response)
        page_list = self.parse_expired(page_list)
        for page in page_list:
            yield scrapy.Request(page.get('url'),callback=self.parse_page_message,meta={'page':page})

        if self.is_next_page:
            next_url = 'https:'+response.xpath('//a[@class="next pagination-item "]/@href').extract_first()
            yield scrapy.Request(next_url,callback=self.parse_page)

    def parse_page_message(self,response):
        postlist = response.xpath('//div[@class="p_postlist"]/div[@class="l_post l_post_bright j_l_post clearfix  "]')
        for post in postlist:
            content_ = post.xpath('.//div[@class="d_post_content j_d_post_content "]').xpath('descendant::text()').extract()
            for i in content_:
                content = ''.join(re.compile(u'[\U00010000-\U0010ffff]').sub('',i.strip()))
            user = post.xpath('.//li[@class="d_name"]/a/text()').extract_first()
            dateline = post.xpath('.//span[@class="tail-info"]/text()').extract()[-1]
            un = str(hash(user+dateline))   #利用用户名和发帖时间去重

            s = Sql()
            try:
                s.save_to_mysql(response.url,user,content,dateline,response.meta['page']['rep_num'],un)
            except:
                pass

        next_page = response.xpath('.//a[contains(.,"下一页")]/@href').extract_first()
        if next_page != None:
            next_page = 'https://tieba.baidu.com'+next_page
            yield scrapy.Request(next_page,callback=self.parse_page_message,meta={'page':response.meta['page']})


cnx = mysql.connector.connect(user='root',password='1234',host='127.0.0.1',database='test')
cur = cnx.cursor(buffered=True)
class Sql:
    @classmethod
    def save_to_mysql(cls,url,user,content,dateline,rep_num,un):
        sql = 'INSERT INTO tieba(`url`,`user`,`content`,`dateline`,`rep_num`,`un`) VALUES (%(url)s,%(user)s,%(content)s,%(dateline)s,%(rep_num)s,%(un)s)'
        value = {
            'url':url,
            'user':user,
            'content': content,
            'dateline': dateline,
            'rep_num': rep_num,
            'un':un,
        }
        cur.execute(sql,value)
        cnx.commit()

