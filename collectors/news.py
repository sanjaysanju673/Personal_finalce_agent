import feedparser


def get_company_news(company):

    query = company.replace(
        " ",
        "+"
    )

    rss_url = (
        f"https://news.google.com/rss/search?"
        f"q={query}+stock"
    )

    feed = feedparser.parse(rss_url)

    articles = []

    for entry in feed.entries[:10]:

        articles.append({
            "title": entry.title,
            "link": entry.link
        })

    return articles