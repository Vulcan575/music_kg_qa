# -*- coding: utf-8 -*-

# Scrapy settings for QQMusicSpider project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://doc.scrapy.org/en/latest/topics/settings.html
#     https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://doc.scrapy.org/en/latest/topics/spider-middleware.html

#BOT_NAME = 'QQMusicSpider'

#SPIDER_MODULES = ['QQMusicSpider.spiders']
#NEWSPIDER_MODULE = 'QQMusicSpider.spiders'

# SINGER_PAGE_NUM = 9809  # 歌手列表的页数
#SINGER_PAGE_NUM = 40    # 歌手列表的页数
#SINGER_PAGE_SIZE = 80  # 歌手列表中，每页歌手的数量
#SONG_PAGE_NUM = 15  # 每个歌手的歌曲爬取的最大页数
#SONG_PAGE_SIZE = 50  # 每个歌手每页爬取多少条歌曲
# SINGER_PAGE_NUM = 3  # 歌手列表的页数
# SINGER_PAGE_SIZE = 80  # 歌手列表中，每页歌手的户数量
# SONG_PAGE_NUM = 3  # 每个歌手的歌曲爬取的最大页数
# SONG_PAGE_SIZE = 10  # 每个歌手每页爬取多少条歌曲

# SONGER_NUM = 1000      # 每个歌手爬取多少条歌曲，最多只能设置1000


# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'QQMusicSpider (+http://www.yourdomain.com)'

# Obey robots.txt rules
#ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://doc.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 1
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# Enable or disable spider middlewares
# See https://doc.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'QQMusicSpider.middlewares.QqmusicspiderSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    'QQMusicSpider.middlewares.QqmusicspiderDownloaderMiddleware': 543,
# }
#DOWNLOADER_MIDDLEWARES = {
#   'QQMusicSpider.middlewares.MyUseragent': 543,
#}

# Enable or disable extensions
# See https://doc.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://doc.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    'QQMusicSpider.pipelines.DuplicatesPipeline': 300,
    'QQMusicSpider.pipelines.QqmusicspiderPipeline': 800,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://doc.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'


# -*- coding: utf-8 -*-

BOT_NAME = 'QQMusicSpider'

SPIDER_MODULES = ['QQMusicSpider.spiders']
NEWSPIDER_MODULE = 'QQMusicSpider.spiders'

SINGER_PAGE_NUM = 40
SINGER_PAGE_SIZE = 80
SONG_PAGE_NUM = 15
SONG_PAGE_SIZE = 100

# ====================== 核心修复：兼容 Scrapy 1.5.1 ======================
ROBOTSTXT_OBEY = False

# 下载延迟（必须慢，防止被封）
DOWNLOAD_DELAY = 3

# 关闭 cookie
COOKIES_ENABLED = False

# 最大并发 = 1（Scrapy 1.5.1 只支持这个全局并发配置）
CONCURRENT_REQUESTS = 1

# 关闭重试
RETRY_ENABLED = False

# 修复 SSL 错误（关键！）
DOWNLOADER_CLIENTCONTEXT_FACTORY = 'scrapy.core.downloader.contextfactory.IgnoreAcceptableCiphersContextFactory'

# 禁用重定向，避免被跳转验证
REDIRECT_ENABLED = False

# 请求头
DEFAULT_REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# ====================== 中间件 & 管道 ======================
DOWNLOADER_MIDDLEWARES = {
    'QQMusicSpider.middlewares.MyUseragent': 543,
}

ITEM_PIPELINES = {
    'QQMusicSpider.pipelines.DuplicatesPipeline': 300, 
    'QQMusicSpider.pipelines.QqmusicspiderPipeline': 800,
}

# ====================== 关闭所有自动加速 ======================
AUTOTHROTTLE_ENABLED = False
HTTPCACHE_ENABLED = False
TELNETCONSOLE_ENABLED = False

