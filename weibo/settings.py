# -*- coding: utf-8 -*-

BOT_NAME = 'weibo'
SPIDER_MODULES = ['weibo.spiders']
NEWSPIDER_MODULE = 'weibo.spiders'
COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False
LOG_LEVEL = 'ERROR'
# 访问完一个页面再访问下一个时需要等待的时间，默认为10秒
DOWNLOAD_DELAY = 1
DEFAULT_REQUEST_HEADERS = {
    'Accept':
    'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-US;q=0.7',
    'cookie':'SINAGLOBAL=2999095678287.9487.1694533442032; SCF=AkR6w_OILlm5cICJ3O0zJLVeILJ5f4DeTub9f3BrVvYSF_2pydkHBUYzyHRUK2BIMIe-bKD94bWqTNjUllWmhng.; SUB=_2A25IfD1YDeRhGeFJ7FoS8CbMyjWIHXVr8DCQrDV8PUNbmtAbLWeikW9NfwF-LFA8xHwv-Dwr7Amd3k3zcmQ4jkBs; SUBP=0033WrSXqPxfM725Ws9jqgMF55529P9D9WhdSJeC9mv91mz1QDEL5rmo5JpX5o275NHD95QNS0MRe05Reh24Ws4DqcjMi--NiK.Xi-2Ri--ciKnRi-zNS0MN1he71h5p1Btt; ALF=1702987655; un=19830432360; WBPSESS=G5zTEiAju-P4VT5VY1Fee02cMa2ODOR0SOuECSzSHz-GtNkp4vbtrsbCub4E5TB_boFL26YXl-zqfEQs_6r-Ye1IIE1SuF4dfv2IWWqZG0ZBMX0FZye3uP3jUfih-H1aRQXsADHxRmQKn9dcQ453bw==; XSRF-TOKEN=bE8w4SfY0nxlE0PzGCsz2u8a; _s_tentry=weibo.com; Apache=5089640387669.39.1702430198621; ULV=1702430198717:5:2:2:5089640387669.39.1702430198621:1702382669871'
}
ITEM_PIPELINES = {
    'weibo.pipelines.DuplicatesPipeline': 300,
    'weibo.pipelines.CsvPipeline': 301,
    # 'weibo.pipelines.MysqlPipeline': 302,
    # 'weibo.pipelines.MongoPipeline': 303,
    # 'weibo.pipelines.MyImagesPipeline': 304,
    # 'weibo.pipelines.MyVideoPipeline': 305
}
# 要搜索的关键词列表，可写多个, 值可以是由关键词或话题组成的列表，也可以是包含关键词的txt文件路径，
# 如'keyword_list.txt'，txt文件中每个关键词占一行
# KEYWORD_LIST = ['????']
KEYWORD_LIST = 'keyword_list.txt'
    #['张瑞敏','柳传志','任正非','李东生','王石']
# 要搜索的微博类型，0代表搜索全部微博，1代表搜索全部原创微博，2代表热门微博，3代表关注人微博，4代表认证用户微博，5代表媒体微博，6代表观点微博
WEIBO_TYPE = 0
# 筛选结果微博中必需包含的内容，0代表不筛选，获取全部微博，1代表搜索包含图片的微博，2代表包含视频的微博，3代表包含音乐的微博，4代表包含短链接的微博
CONTAIN_TYPE = 0
# 筛选微博的发布地区，精确到省或直辖市，值不应包含“省”或“市”等字，如想筛选北京市的微博请用“北京”而不是“北京市”，想要筛选安徽省的微博请用“安徽”而不是“安徽省”，可以写多个地区，
# 具体支持的地名见region.py文件，注意只支持省或直辖市的名字，省下面的市名及直辖市下面的区县名不支持，不筛选请用“全部”
REGION = ['全部']
# 搜索的起始日期，为yyyy-mm-dd形式，搜索结果包含该日期
START_DATE = '2020-01-01'
# 搜索的终止日期，为yyyy-mm-dd形式，搜索结果包含该日期
END_DATE = '2020-12-31'
# 进一步细分搜索的阈值，若结果页数大于等于该值，则认为结果没有完全展示，细分搜索条件重新搜索以获取更多微博。数值越大速度越快，也越有可能漏掉微博；数值越小速度越慢，获取的微博就越多。
# 建议数值大小设置在40到50之间。
FURTHER_THRESHOLD = 2
# 图片文件存储路径
IMAGES_STORE = './'
# 视频文件存储路径
FILES_STORE = './'
# 配置MongoDB数据库
# MONGO_URI = 'localhost'
# 配置MySQL数据库，以下为默认配置，可以根据实际情况更改，程序会自动生成一个名为weibo的数据库，如果想换其它名字请更改MYSQL_DATABASE值
# MYSQL_HOST = 'localhost'
# MYSQL_PORT = 3306
# MYSQL_USER = 'root'
# MYSQL_PASSWORD = '123456'
# MYSQL_DATABASE = 'weibo'
