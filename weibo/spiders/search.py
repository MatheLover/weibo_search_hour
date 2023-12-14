# -*- coding: utf-8 -*-
import os
import re
import sys
from datetime import datetime, timedelta
from urllib.parse import unquote

import scrapy
import weibo.utils.util as util
from scrapy.exceptions import CloseSpider
from scrapy.utils.project import get_project_settings
from weibo.items import WeiboItem
import logging

# --- create log file --- #
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# 消息格式化
formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y/%m/%d %H:%M:%S')

# 日志文件输出
fh = logging.FileHandler('../weibo_search_hour/' + __name__ + '.log')
fh.setFormatter(formatter)
logger.addHandler(fh)


class SearchSpider(scrapy.Spider):
    # initial setup including domains
    name = 'search'
    allowed_domains = ['weibo.com']
    settings = get_project_settings()

    # post counter
    counting = 0

    # initialize keyword list
    keyword_list = settings.get('KEYWORD_LIST')
    if not isinstance(keyword_list, list):
        if not os.path.isabs(keyword_list):
            keyword_list = os.getcwd() + os.sep + keyword_list
        if not os.path.isfile(keyword_list):
            sys.exit('不存在%s文件' % keyword_list)
        keyword_list = util.get_keyword_list(keyword_list)
    for i, keyword in enumerate(keyword_list):
        if len(keyword) > 2 and keyword[0] == '#' and keyword[-1] == '#':
            keyword_list[i] = '%23' + keyword[1:-1] + '%23'

    # get info from settings.py
    weibo_type = util.convert_weibo_type(settings.get('WEIBO_TYPE'))
    contain_type = util.convert_contain_type(settings.get('CONTAIN_TYPE'))
    regions = util.get_regions(settings.get('REGION'))
    base_url = 'https://s.weibo.com'
    start_date = settings.get('START_DATE',
                              datetime.now().strftime('%Y-%m-%d'))
    end_date = settings.get('END_DATE', datetime.now().strftime('%Y-%m-%d'))
    if util.str_to_time(start_date) > util.str_to_time(end_date):
        sys.exit('settings.py配置错误，START_DATE值应早于或等于END_DATE值，请重新配置settings.py')
    further_threshold = settings.get('FURTHER_THRESHOLD', 46)
    mongo_error = False
    pymongo_error = False
    mysql_error = False
    pymysql_error = False

    # initialize start and end dates in  yy-mm-dd-hh format
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date,
                                 '%Y-%m-%d')
    start_str = start_date.strftime('%Y-%m-%d') + '-0'
    end_str = end_date.strftime('%Y-%m-%d') + '-0'
    end_date_2 = datetime.strptime(end_str, '%Y-%m-%d-%H')
    start_date_2 = datetime.strptime(start_str, '%Y-%m-%d-%H')

    # set up url variable and later it will be assigned as base_url + self.weibo_type + self.contain_type
    # e.g. 'https://s.weibo.com/weibo?q=香港&typeall=1&suball=1'
    constant_url = ''

    def start_requests(self):
        # iterate each keyword
        for keyword in self.keyword_list:

            # log keyword
            logger.info('keyword searching: ' + keyword)

            # for all provinces
            if not self.settings.get('REGION') or '全部' in self.settings.get(
                    'REGION'):

                # construct url excluding start and end dates
                base_url = 'https://s.weibo.com/weibo?q=%s' % keyword
                url = base_url + self.weibo_type
                self.constant_url = url + self.contain_type

                # construct url in one-hour manner and perform search
                # 2020-09-01-13:2020-09-01-14 means 2020-09-01 13:00 to 2020-09-01 14:00
                # e.g. https://s.weibo.com/weibo?q=连花清瘟&typeall=1&suball=1&timescope=custom:2020-09-01-13:2020-09-01-14
                # start_date should not exceed the end date
                while self.start_date_2 < self.end_date_2:

                    #  Note: If start date is 2020-09-01 and end date is 2020-09-02,
                    #  the whole period starts from 2020-09-01-0 and ends at 2020-09-02-0
                    for i in range(1, 25):
                        # process start and end time
                        start_str, end_str = self.date_processing()

                        # construct url with start and end time in 1 hour
                        start_url = self.constant_url + '&timescope=custom:{}:{}'.format(start_str, end_str)


                        # make request to start_url and call parse method for its response
                        yield scrapy.Request(url=start_url,
                                             callback=self.parse,
                                             meta={
                                                 'base_url': base_url,
                                                 'keyword': keyword
                                             })
            else:
                # for each province
                for region in self.regions.values():

                    # construct region-based url without start and end time
                    base_url = (
                        'https://s.weibo.com/weibo?q={}&region=custom:{}:1000'
                    ).format(keyword, region['code'])
                    url = base_url + self.weibo_type
                    self.constant_url = url + self.contain_type

                    # same as above
                    while self.start_date_2 < self.end_date_2:
                        for i in range(1, 25):
                            start_str, end_str = self.date_processing()
                            start_url = self.constant_url + '&timescope=custom:{}:{}'.format(start_str, end_str)


                            # add province in meta
                            yield scrapy.Request(url=start_url,
                                                 callback=self.parse,
                                                 meta={
                                                     'base_url': base_url,
                                                     'keyword': keyword,
                                                     'province': region
                                                 })

            # reset start date for next keyword
            self.start_date_2 = datetime.strptime(self.start_str, '%Y-%m-%d-%H')

    def check_environment(self):
        """判断配置要求的软件是否已安装"""
        if self.pymongo_error:
            print('系统中可能没有安装pymongo库，请先运行 pip install pymongo ，再运行程序')
            raise CloseSpider()
        if self.mongo_error:
            print('系统中可能没有安装或启动MongoDB数据库，请先根据系统环境安装或启动MongoDB，再运行程序')
            raise CloseSpider()
        if self.pymysql_error:
            print('系统中可能没有安装pymysql库，请先运行 pip install pymysql ，再运行程序')
            raise CloseSpider()
        if self.mysql_error:
            print('系统中可能没有安装或正确配置MySQL数据库，请先根据系统环境安装或配置MySQL，再运行程序')
            raise CloseSpider()

    def parse(self, response):
        """Construct urls for all result pages of each search with a specific timeslot(e.g.https://s.weibo.com/weibo?q=连花清瘟&typeall=1&suball=1&timescope=custom:2020-09-01-13:2020-09-01-14 )
        recursively and call parse_weibo method to process each result page """

        # retrieve keywords
        keyword = response.meta.get('keyword')

        # whether the page is empty
        is_empty = response.xpath(
            '//div[@class="card card-no-result s-pt20b40"]')

        # number of result pages for each search within a specific timeslot
        page_count = len(response.xpath('//ul[@class="s-scroll"]/li'))

        # empty
        if is_empty:
            # log empty warning
            logger.warning('当前页面搜索结果为空 '+response.url)
        else:
            # if 1-page result
            if page_count == 0:
                try:
                    # period
                    period = response.xpath('//span[@class="ctips"]//text()').extract_first()

                    # log 1 page result info
                    logger.info(
                        keyword + " " + period + " 1" + "pages")
                except:
                    print("No period information or period information is abnormal")
            else:
                try:
                    # period_2
                    period_2 = response.xpath('//span[@class="ctips"]//text()').extract_first()

                    # log (page_count) results
                    logger.info(
                        keyword + " " + period_2 + " " + str(
                            page_count) + "pages")
                except:
                    print("No period information or period information is abnormal")

            # process the current page
            for weibo in self.parse_weibo(response):
                # check software dependency
                self.check_environment()

                # yield weibo
                yield weibo

            # find next page url
            next_url = response.xpath(
                '//a[@class="next"]/@href').extract_first()

            # if next url exists
            if next_url:
                # note: use 'https://s.weibo.com' in this case; self is required
                next_url = self.base_url + next_url

                # make request to next url and recursively call parse method
                yield scrapy.Request(url=next_url,
                                     callback=self.parse,
                                     meta={'keyword': keyword})

    def get_article_url(self, selector):
        """获取微博头条文章url"""
        article_url = ''
        text = selector.xpath('string(.)').extract_first().replace(
            '\u200b', '').replace('\ue627', '').replace('\n',
                                                        '').replace(' ', '')
        if text.startswith('发布了头条文章'):
            urls = selector.xpath('.//a')
            for url in urls:
                if url.xpath(
                        'i[@class="wbicon"]/text()').extract_first() == 'O':
                    if url.xpath('@href').extract_first() and url.xpath(
                            '@href').extract_first().startswith('http://t.cn'):
                        article_url = url.xpath('@href').extract_first()
                    break
        return article_url

    def get_location(self, selector):
        """获取微博发布位置"""
        a_list = selector.xpath('.//a')
        location = ''
        for a in a_list:
            if a.xpath('./i[@class="wbicon"]') and a.xpath(
                    './i[@class="wbicon"]/text()').extract_first() == '2':
                location = a.xpath('string(.)').extract_first()[1:]
                break
        return location

    def get_at_users(self, selector):
        """获取微博中@的用户昵称"""
        a_list = selector.xpath('.//a')
        at_users = ''
        at_list = []
        for a in a_list:
            if len(unquote(a.xpath('@href').extract_first())) > 14 and len(
                    a.xpath('string(.)').extract_first()) > 1:
                if unquote(a.xpath('@href').extract_first())[14:] == a.xpath(
                        'string(.)').extract_first()[1:]:
                    at_user = a.xpath('string(.)').extract_first()[1:]
                    if at_user not in at_list:
                        at_list.append(at_user)
        if at_list:
            at_users = ','.join(at_list)
        return at_users

    def get_topics(self, selector):
        """获取参与的微博话题"""
        a_list = selector.xpath('.//a')
        topics = ''
        topic_list = []
        for a in a_list:
            text = a.xpath('string(.)').extract_first()
            if len(text) > 2 and text[0] == '#' and text[-1] == '#':
                if text[1:-1] not in topic_list:
                    topic_list.append(text[1:-1])
        if topic_list:
            topics = ','.join(topic_list)
        return topics

    def date_processing(self):
        """ Return the start time and end time for each hour, e.g. 2020-09-01-13 and 2020-09-01-14"""

        # start time e.g. 2020-09-01-13:00
        start_str = self.start_date_2.strftime('%Y-%m-%d-X%H').replace(
            'X0', 'X').replace('X', '')

        # update to obtain end time e.g. 2020-09-01-14:00
        self.start_date_2 = self.start_date_2 + timedelta(hours=1)

        # format end time
        end_str = self.start_date_2.strftime('%Y-%m-%d-X%H').replace(
            'X0', 'X').replace('X', '')

        return start_str, end_str

    def parse_weibo(self, response):
        """解析网页中的微博信息"""
        keyword = response.meta.get('keyword')

        # for each post on the page
        for sel in response.xpath("//div[@class='card-wrap']"):
            # enter into more detail
            info = sel.xpath(
                "div[@class='card']/div[@class='card-feed']/div[@class='content']/div[@class='info']"
            )

            # extract different info
            if info:
                weibo = WeiboItem()
                weibo['id'] = sel.xpath('@mid').extract_first()
                try:
                    weibo['bid'] = sel.xpath(
                        './/p[@class="from"]/a[1]/@href').extract_first(
                    ).split('/')[-1].split('?')[0]
                except:
                    weibo['bid'] = sel.xpath(
                        './/div[@class="from"]/a[1]/@href').extract_first(
                    ).split('/')[-1].split('?')[0]
                weibo['user_id'] = info[0].xpath(
                    'div[2]/a/@href').extract_first().split('?')[0].split(
                    '/')[-1]
                weibo['screen_name'] = info[0].xpath(
                    'div[2]/a/@nick-name').extract_first()
                txt_sel = sel.xpath('.//p[@class="txt"]')[0]
                retweet_sel = sel.xpath('.//div[@class="card-comment"]')
                retweet_txt_sel = ''
                if retweet_sel and retweet_sel[0].xpath('.//p[@class="txt"]'):
                    retweet_txt_sel = retweet_sel[0].xpath(
                        './/p[@class="txt"]')[0]
                content_full = sel.xpath(
                    './/p[@node-type="feed_list_content_full"]')
                is_long_weibo = False
                is_long_retweet = False
                if content_full:
                    if not retweet_sel:
                        txt_sel = content_full[0]
                        is_long_weibo = True
                    elif len(content_full) == 2:
                        txt_sel = content_full[0]
                        retweet_txt_sel = content_full[1]
                        is_long_weibo = True
                        is_long_retweet = True
                    elif retweet_sel[0].xpath(
                            './/p[@node-type="feed_list_content_full"]'):
                        retweet_txt_sel = retweet_sel[0].xpath(
                            './/p[@node-type="feed_list_content_full"]')[0]
                        is_long_retweet = True
                    else:
                        txt_sel = content_full[0]
                        is_long_weibo = True
                weibo['text'] = txt_sel.xpath(
                    'string(.)').extract_first().replace('\u200b', '').replace(
                    '\ue627', '')
                weibo['article_url'] = self.get_article_url(txt_sel)
                weibo['location'] = self.get_location(txt_sel)
                if weibo['location']:
                    weibo['text'] = weibo['text'].replace(
                        '2' + weibo['location'], '')
                weibo['text'] = weibo['text'][2:].replace(' ', '')
                if is_long_weibo:
                    weibo['text'] = weibo['text'][:-4]
                weibo['at_users'] = self.get_at_users(txt_sel)
                weibo['topics'] = self.get_topics(txt_sel)
                reposts_count = sel.xpath(
                    './/a[@action-type="feed_list_forward"]/text()').extract()
                reposts_count = "".join(reposts_count)
                try:
                    reposts_count = re.findall(r'\d+.*', reposts_count)
                except TypeError:
                    logger.error(
                        "无法解析转发按钮，可能是 1) 网页布局有改动 2) cookie无效或已过期。\n"
                        "请在 https://github.com/dataabc/weibo-search 查看文档，以解决问题，"
                    )
                    raise CloseSpider()
                weibo['reposts_count'] = reposts_count[
                    0] if reposts_count else '0'
                comments_count = sel.xpath(
                    './/a[@action-type="feed_list_comment"]/text()'
                ).extract_first()
                try:
                    comments_count = re.findall(r'\d+.*', comments_count)
                except:
                    comments_count = 0
                weibo['comments_count'] = comments_count[
                    0] if comments_count else '0'
                attitudes_count = sel.xpath(
                    '(.//span[@class="woo-like-count"])[last()]/text()').extract_first()
                attitudes_count = re.findall(r'\d+.*', attitudes_count)
                weibo['attitudes_count'] = attitudes_count[
                    0] if attitudes_count else '0'
                try:
                    created_at = sel.xpath(
                        './/p[@class="from"]/a[1]/text()').extract_first(
                    ).replace(' ', '').replace('\n', '').split('前')[0]
                except:
                    created_at = sel.xpath(
                        './/div[@class="from"]/a[1]/text()').extract_first(
                    ).replace(' ', '').replace('\n', '').split('前')[0]
                weibo['created_at'] = util.standardize_date(created_at)
                try:
                    source = sel.xpath('.//p[@class="from"]/a[2]/text()'
                                       ).extract_first()
                except:
                    source = sel.xpath('.//div[@class="from"]/a[2]/text()'
                                       ).extract_first()
                weibo['source'] = source if source else ''
                pics = ''
                is_exist_pic = sel.xpath(
                    './/div[@class="media media-piclist"]')
                if is_exist_pic:
                    pics = is_exist_pic[0].xpath('ul[1]/li/img/@src').extract()
                    pics = [pic[8:] for pic in pics]
                    pics = [
                        re.sub(r'/.*?/', '/large/', pic, 1) for pic in pics
                    ]
                    pics = ['https://' + pic for pic in pics]
                video_url = ''
                is_exist_video = sel.xpath(
                    './/div[@class="thumbnail"]//video-player').extract_first()
                if is_exist_video:
                    video_url = re.findall(r'src:\'(.*?)\'', is_exist_video)[0]
                    video_url = video_url.replace('&amp;', '&')
                    video_url = 'http:' + video_url
                if not retweet_sel:
                    weibo['pics'] = pics
                    weibo['video_url'] = video_url
                else:
                    weibo['pics'] = ''
                    weibo['video_url'] = ''
                weibo['retweet_id'] = ''
                if retweet_sel and retweet_sel[0].xpath(
                        './/div[@node-type="feed_list_forwardContent"]/a[1]'):
                    retweet = WeiboItem()
                    retweet['id'] = retweet_sel[0].xpath(
                        './/a[@action-type="feed_list_like"]/@action-data'
                    ).extract_first()[4:]
                    try:
                        retweet['bid'] = retweet_sel[0].xpath(
                            './/p[@class="from"]/a/@href').extract_first().split(
                            '/')[-1].split('?')[0]
                    except:
                        retweet['bid'] = retweet_sel[0].xpath(
                            './/div[@class="from"]/a/@href').extract_first().split(
                            '/')[-1].split('?')[0]
                    info = retweet_sel[0].xpath(
                        './/div[@node-type="feed_list_forwardContent"]/a[1]'
                    )[0]
                    retweet['user_id'] = info.xpath(
                        '@href').extract_first().split('/')[-1]
                    retweet['screen_name'] = info.xpath(
                        '@nick-name').extract_first()
                    retweet['text'] = retweet_txt_sel.xpath(
                        'string(.)').extract_first().replace('\u200b',
                                                             '').replace(
                        '\ue627', '')
                    retweet['article_url'] = self.get_article_url(
                        retweet_txt_sel)
                    retweet['location'] = self.get_location(retweet_txt_sel)
                    if retweet['location']:
                        retweet['text'] = retweet['text'].replace(
                            '2' + retweet['location'], '')
                    retweet['text'] = retweet['text'][2:].replace(' ', '')
                    if is_long_retweet:
                        retweet['text'] = retweet['text'][:-4]
                    retweet['at_users'] = self.get_at_users(retweet_txt_sel)
                    retweet['topics'] = self.get_topics(retweet_txt_sel)
                    reposts_count = retweet_sel[0].xpath(
                        './/ul[@class="act s-fr"]/li[1]/a[1]/text()'
                    ).extract_first()
                    reposts_count = re.findall(r'\d+.*', reposts_count)
                    retweet['reposts_count'] = reposts_count[
                        0] if reposts_count else '0'
                    comments_count = retweet_sel[0].xpath(
                        './/ul[@class="act s-fr"]/li[2]/a[1]/text()'
                    ).extract_first()
                    comments_count = re.findall(r'\d+.*', comments_count)
                    retweet['comments_count'] = comments_count[
                        0] if comments_count else '0'
                    attitudes_count = retweet_sel[0].xpath(
                        './/a[@class="woo-box-flex woo-box-alignCenter woo-box-justifyCenter"]//span[@class="woo-like-count"]/text()'
                    ).extract_first()
                    attitudes_count = re.findall(r'\d+.*', attitudes_count)
                    retweet['attitudes_count'] = attitudes_count[
                        0] if attitudes_count else '0'
                    created_at = retweet_sel[0].xpath(
                        './/p[@class="from"]/a[1]/text()').extract_first(
                    ).replace(' ', '').replace('\n', '').split('前')[0]
                    retweet['created_at'] = util.standardize_date(created_at)
                    source = retweet_sel[0].xpath(
                        './/p[@class="from"]/a[2]/text()').extract_first()
                    retweet['source'] = source if source else ''
                    retweet['pics'] = pics
                    retweet['video_url'] = video_url
                    retweet['retweet_id'] = ''
                    yield {'weibo': retweet, 'keyword': keyword}
                    weibo['retweet_id'] = retweet['id']
                self.counting = self.counting + 1

                # print progress for every 500 posts
                if (self.counting % 500 == 0):
                    logger.info('work in progress. posts count: ' + str(self.counting))
                    logger.info(weibo)
                    print(weibo)
                    print('work in progress. posts count: ' + str(self.counting))
                yield {'weibo': weibo, 'keyword': keyword}

    def close(self, reason):
        """Record program duration"""
        start_time = self.crawler.stats.get_value('start_time')
        finish_time = self.crawler.stats.get_value('finish_time')
        print("Total run time: ", finish_time - start_time, " (hour:min:sec) ")
