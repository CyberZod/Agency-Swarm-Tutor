import os
import asyncio
import requests
import re
import html2text
from xml.etree import ElementTree
from typing import List, Optional
from agency_swarm.tools import BaseTool
from pydantic import Field
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

class WebsiteScraperTool(BaseTool):
    """
    A tool for scraping all pages of a website using its sitemap.
    Converts scraped HTML into clean Markdown files.
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
        Fetches sitemap URLs, scrapes content, and saves as markdown files.

        Returns:
            List[str]: List of saved markdown file paths.
        """
        urls = self.get_sitemap_urls()
        if not urls:
            return ["No URLs found to scrape."]

        scraped_data = await self.crawl_parallel(urls, self.max_concurrent)
        saved_files = self.save_to_markdown(scraped_data)
        return saved_files

    def get_sitemap_urls(self) -> List[str]:
        """Fetches all URLs from the website's sitemap."""
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

    async def crawl_parallel(self, urls: List[str], max_concurrent: int) -> List[dict]:
        """Crawls pages in parallel batches."""
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
                        scraped_data.append({"url": url, "html": result.html})

        finally:
            await crawler.close()

        return scraped_data

    def save_to_markdown(self, scraped_data: List[dict]) -> List[str]:
        """Converts HTML content to Markdown and saves as .md files."""
        output_dir = "scraped_content"
        os.makedirs(output_dir, exist_ok=True)
        saved_files = []

        for data in scraped_data:
            url = data["url"]
            html_content = data["html"]

            # Convert HTML to Markdown
            markdown_content = html2text.html2text(html_content)

            # Generate a safe filename from the URL
            filename = re.sub(r'[<>:"/\\|?*]', '_', url.replace("https://", "").replace("http://", "")) + ".md"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# Scraped Content from {url}\n\n")
                f.write(markdown_content)

            saved_files.append(filepath)

        print(f"\nSaved {len(saved_files)} pages to '{output_dir}'")
        return saved_files


if __name__ == "__main__":
    tool = WebsiteScraperTool(website_url="https://ai.pydantic.dev", max_concurrent=10)
    print(asyncio.run(tool.run()))
