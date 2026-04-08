"""
DocSearch scraper main entry point
"""
import os
import json
import requests
from requests_iap import IAPAuth

from scrapy.crawler import CrawlerProcess

from .algolia_helper import AlgoliaHelper
from .config.config_loader import ConfigLoader
from .documentation_spider import DocumentationSpider
from .strategies.default_strategy import DefaultStrategy
from .custom_downloader_middleware import CustomDownloaderMiddleware
from .custom_dupefilter import CustomDupeFilter
from .config.browser_handler import BrowserHandler
from .strategies.algolia_settings import AlgoliaSettings

try:
    # disable boto (S3 download)
    from scrapy import optional_features

    if 'boto' in optional_features:
        optional_features.remove('boto')
except ImportError:
    pass

EXIT_CODE_NO_RECORD = 3


def run_config(config):
    config = ConfigLoader(config)
    CustomDownloaderMiddleware.driver = config.driver
    DocumentationSpider.NB_INDEXED = 0

    strategy = DefaultStrategy(config)

    algolia_helper = AlgoliaHelper(
        config.app_id,
        config.api_key,
        config.index_name,
        config.index_name_tmp,
        AlgoliaSettings.get(config, strategy.levels),
        config.query_rules,
        config.current_product,
        config.current_version
    )

    root_module = 'src.' if __name__ == '__main__' else 'scraper.src.'
    DOWNLOADER_MIDDLEWARES_PATH = root_module + 'custom_downloader_middleware.' + CustomDownloaderMiddleware.__name__
    DUPEFILTER_CLASS_PATH = root_module + 'custom_dupefilter.' + CustomDupeFilter.__name__

    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en",
    }  # Defaults for scrapy https://docs.scrapy.org/en/latest/topics/settings.html#default-request-headers

    if os.getenv("CF_ACCESS_CLIENT_ID") and os.getenv("CF_ACCESS_CLIENT_SECRET"):
        headers.update(
            {
                "CF-Access-Client-Id": os.getenv("CF_ACCESS_CLIENT_ID"),
                "CF-Access-Client-Secret": os.getenv("CF_ACCESS_CLIENT_SECRET"),
            }
        )
    elif os.getenv("IAP_AUTH_CLIENT_ID") and os.getenv("IAP_AUTH_SERVICE_ACCOUNT_JSON"):
        iap_token = IAPAuth(
            client_id=os.getenv("IAP_AUTH_CLIENT_ID"),
            service_account_secret_dict=json.loads(
                os.getenv("IAP_AUTH_SERVICE_ACCOUNT_JSON")
            ),
        )(requests.Request()).headers["Authorization"]
        headers.update({"Authorization": iap_token})

    DEFAULT_REQUEST_HEADERS = headers

    process = CrawlerProcess({
        'LOG_ENABLED': '1',
        'LOG_LEVEL': 'ERROR',
        'USER_AGENT': config.user_agent,
        'DOWNLOADER_MIDDLEWARES': {DOWNLOADER_MIDDLEWARES_PATH: 900},
        # Need to be > 600 to be after the redirectMiddleware
        'DUPEFILTER_USE_ANCHORS': config.use_anchors,
        # Use our custom dupefilter in order to be scheme agnostic regarding link provided
        'DUPEFILTER_CLASS': DUPEFILTER_CLASS_PATH,
        'DEFAULT_REQUEST_HEADERS': DEFAULT_REQUEST_HEADERS,
        'TELNETCONSOLE_ENABLED': False
    })

    process.crawl(
        DocumentationSpider,
        config=config,
        algolia_helper=algolia_helper,
        strategy=strategy
    )

    process.start()
    process.stop()

    # Kill browser if needed
    BrowserHandler.destroy(config.driver)

    if len(config.extra_records) > 0:
        algolia_helper.add_records(config.extra_records, "Extra records", False)

    print("")

    if DocumentationSpider.NB_INDEXED > 0:
        algolia_helper.commit_tmp_index()
        print('Nb hits: {}'.format(DocumentationSpider.NB_INDEXED))
        config.update_nb_hits_value(DocumentationSpider.NB_INDEXED)
    else:
        print('Crawling issue: nbHits 0 for ' + config.index_name)
        exit(EXIT_CODE_NO_RECORD)
    print("")


if __name__ == '__main__':
    import sys
    _, product, version = sys.argv
    config_name = 'config'
    if product == 'mqttx':
        config_name = 'mqttx-config'
    elif product.startswith('datalayers'):
        config_name = 'datalayers-config'

    base_url = os.environ.get('BASE_URL', 'https://docs.emqx.com')
    config_dict = json.load(open(f'{config_name}.json', 'r'))
    if product == 'broker':
        config_dict['index_name'] = 'emqx'
        config_dict['sitemap_urls'] = [f'https://www.emqx.io/docs/sitemap_{version}.xml']
    elif product == 'emqx':
        config_dict['index_name'] = 'emqx'
        config_dict['sitemap_urls'] = [f'https://docs.emqx.com/sitemap_emqx_{version}.xml']
    elif product == 'nanomq':
        config_dict['index_name'] = 'nanomq'
        config_dict['sitemap_urls'] = [f'https://nanomq.io/docs/sitemap_{version}.xml']
    elif product == 'ekuiper':
        config_dict['index_name'] = 'ekuiper'
        config_dict['sitemap_urls'] = [f'https://ekuiper.org/docs/sitemap_{version}.xml']
    elif product == 'hstreamdb':
        config_dict['sitemap_urls'] = [f'https://hstream.io/docs/sitemap_{version}.xml']
    elif product == 'datalayers-docs-zh':
        product = 'datalayers'
        config_dict['index_name'] = 'zh'
        config_dict['sitemap_urls'] = [f'https://docs.datalayers.cn/sitemap_datalayers_{version}.xml']
    elif product == 'datalayers-docs-en':
        product = 'datalayers'
        config_dict['index_name'] = 'en'
        config_dict['sitemap_urls'] = [f'https://docs.datalayers.io/sitemap_datalayers_{version}.xml']
    elif product == 'mqttx':
        config_dict['index_name'] = 'mqttx'
        # config_dict['sitemap_urls'] = ['https://mqttx.app/sitemap.xml']
    else:
        config_dict['sitemap_urls'] = [f'{base_url}/sitemap_{product}_{version}.xml']

    if product == 'enterprise':
        config_dict['stop_urls'] = [
            'https://docs.emqx.com/zh/enterprise/.*/hocon/',
            'https://docs.emqx.com/en/enterprise/.*/hocon/'
        ]
    elif product == 'broker':
        config_dict['stop_urls'] = [
            'https://www.emqx.io/docs/zh/.*/hocon/',
            'https://www.emqx.io/docs/en/.*/hocon/'
        ]
    elif product == 'emqx':
        config_dict['stop_urls'] = [
            'https://docs.emqx.com/zh/emqx/.*/hocon/',
            'https://docs.emqx.com/en/emqx/.*/hocon/'
        ]

    config_dict.update({
        'current_product': product,
        'current_version': version
    })
    print('Run config: ', config_dict)
    run_config(json.dumps(config_dict))
