# Offer Pool

Course project of Web and Text Mining

## Setup

1. You will need to download the ChromeDriver executable from http://chromedriver.storage.googleapis.com/index.html.

2. Install dependencies: `selenium`. If you have pipenv installed, you can run `pipenv install` to install all dependencies.

3. Run the crawler: `python crawler.py`.

You can set an environment variable `OFFERPOOL_CRAWLER_START_PAGE` and `OFFERPOOL_CRAWLER_END_PAGE` to specify the beginning page and the end page to scrape (default: page 1 - page 5).