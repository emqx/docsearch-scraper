"""CustomDownloaderMiddleware"""
from urllib.parse import urlparse


class CustomDownloaderMiddleware:
    def process_response(self, request, response, spider):
        if spider.remove_get_params:
            o = urlparse(response.url)
            url_without_params = o.scheme + '://' + o.netloc + o.path
            response = response.replace(url=url_without_params)

        if response.url == request.url + '#':
            response = response.replace(url=request.url)

        return response
