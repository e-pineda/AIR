from scrapy import cmdline
cmdline.execute("scrapy crawl genius -o test_output.csv".split())

# cmdline.execute("scrapy crawl bpm".split())
