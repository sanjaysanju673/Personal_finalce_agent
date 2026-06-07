import feedparser
import socket
from config.logging_config import get_logger

logger = get_logger(__name__)

# Set timeout for socket operations
socket.setdefaulttimeout(10)

def get_company_news(company):
    logger.debug(f"Fetching news for {company}")
    try:
        query = company.replace(
            " ",
            "+"
        )

        rss_url = (
            f"https://news.google.com/rss/search?"
            f"q={query}+stock"
        )

        logger.debug(f"Fetching from RSS URL: {rss_url}")
        feed = feedparser.parse(rss_url)

        articles = []

        if hasattr(feed, 'entries') and feed.entries:
            logger.info(f"Found {len(feed.entries)} articles for {company}")
            for entry in feed.entries[:10]:
                try:
                    articles.append({
                        "title": entry.get('title', 'N/A'),
                        "link": entry.get('link', '#')
                    })
                except:
                    continue
        else:
            logger.warning(f"No entries found in feed for {company}")

        logger.info(f"Successfully fetched {len(articles)} news articles for {company}")
        return articles
    
    except (socket.timeout, Exception) as e:
        logger.warning(f"Could not fetch news for {company}: {str(e)}")
        return []