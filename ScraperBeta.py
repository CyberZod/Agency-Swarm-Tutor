import os
import asyncio
import requests
from xml.etree import ElementTree
from typing import List, Optional
from agency_swarm.tools import BaseTool
from pydantic import Field
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

class WebsiteScraperTool(BaseTool):
    """
    A tool for scraping all pages of a website using its sitemap.
    This tool fetches URLs from the sitemap and scrapes them in parallel batches.
    """

    website_url: str = Field(
        ..., description="The base URL of the website to scrape. Example: 'https://example.com'"
    )
    max_concurrent: Optional[int] = Field(
        5, description="The maximum number of concurrent scraping tasks."
    )

    async def run(self) -> List[str]:
        """
        Runs the website scraper tool.
        It first fetches the sitemap URLs and then crawls them in parallel.

        Returns:
            List[str]: A list of scraped page contents.
        """
        urls = self.get_sitemap_urls()
        if not urls:
            return ["No URLs found to scrape."]

        return await self.crawl_parallel(urls, self.max_concurrent)

    def get_sitemap_urls(self) -> List[str]:
        """
        Fetches all URLs from the website's sitemap.

        Returns:
            List[str]: List of URLs.
        """
        sitemap_url = f"{self.website_url.rstrip('/')}/sitemap.xml"
        try:
            response = requests.get(sitemap_url)
            response.raise_for_status()

            root = ElementTree.fromstring(response.content)
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            urls = [loc.text for loc in root.findall('.//ns:loc', namespace)]

            return urls
        except Exception as e:
            print(f"Error fetching sitemap: {e}")
            return []

    async def crawl_parallel(self, urls: List[str], max_concurrent: int) -> List[str]:
        """
        Crawls pages in parallel batches.

        Args:
            urls (List[str]): The list of URLs to crawl.
            max_concurrent (int): Number of concurrent tasks.

        Returns:
            List[str]: List of scraped page contents.
        """
        print("\n=== Starting Parallel Crawling ===")

        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
            extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
        )
        crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

        crawler = AsyncWebCrawler(config=browser_config)
        await crawler.start()
        scraped_data = []

        try:
            for i in range(0, len(urls), max_concurrent):
                batch = urls[i : i + max_concurrent]
                tasks = [crawler.arun(url, crawl_config, f"session_{i + j}") for j, url in enumerate(batch)]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for url, result in zip(batch, results):
                    if isinstance(result, Exception):
                        print(f"Error scraping {url}: {result}")
                    elif result.success:
                        scraped_data.append(result.html)

        finally:
            await crawler.close()

        return scraped_data


if __name__ == "__main__":
    tool = WebsiteScraperTool(website_url="https://ai.pydantic.dev", max_concurrent=10)
    check = asyncio.run(tool.run())
    if check:
        print("Success")
    else:
        print("Failed")