from scrapy import cmdline
cmdline.execute("scrapy crawl genius -o yeet_rapper_scrape.csv".split())

cmdline.execute("scrapy crawl bpm".split())
