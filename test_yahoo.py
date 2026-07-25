from market_sentinel.collectors.yahoo.collector import YahooCollector

collector = YahooCollector()

quotes = collector.collect()

print()

print("=" * 60)

for q in quotes:
    print(q)