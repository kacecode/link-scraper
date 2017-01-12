from collections import namedtuple
from urllib.parse import urlparse

import scrapy


Link = namedtuple('Link', ['local', 'url'])


class LinkSpider(scrapy.Spider):
    """
    Crawls from a source URL, storing the links into a collection for analysis.
    """
    name = "links"

    def start_requests(self):
        url = "http://izeni.com"
        self.store = LinkCollector(url)
        self.visited = set()

        yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        # Find links
        raw_links = response.css('a').xpath('@href').extract()
        # Add to collector
        for i in raw_links:
            if i.startswith('..'):
                continue
            is_local = self.store.add(i)
            if is_local.local and is_local.url not in self.visited:
                self.visited.add(is_local.url)
                yield scrapy.Request(is_local.url, self.parse)

    def closed(self, reason):
        print(self.store)


class LinkCollector:
    """
    Aggregates saving off a list of links.
    """
    def __init__(self, root_url):
        self.data = set()
        self.root_url = root_url.strip().lower()

    def normalize_link(self, link):
        """
        Resolves urls to fully qualified paths.
        """
        result = urlparse(link.strip().lower())
        absolute = bool(result.netloc)

        # If relative ref (e.g. /foo)
        template = '{}{}' if link.startswith('/') else '{}/{}'
        to_save = template.format(self.root_url, result.path) if not absolute \
            else result.geturl()

        return to_save

    def add(self, link):
        """
        Adds a URL to the collection.
        """
        normal = self.normalize_link(link)
        self.data.add(normal)

        return Link(normal.startswith(self.root_url), normal)

    def __str__(self):
        return str(self.data)
