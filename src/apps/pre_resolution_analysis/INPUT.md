# Input Prompt

I want to have a dashboard, for the last N days of historical data, find trades where price was higher than X (default is 0.98) Y minutes (default 2 minutes) before the resolution, and check how often the last known price was higher than that. You can use polymarket_order_filled table, because we don't need maker-taker here.

Output is a pie chart, and some analysis text, like: Probability of winning is 0.95, meaning that in 95 cases out of 100 you are winning (1.0 - X (user input)) and in 5 cases you are losing X. So your EV is ...

## Updates
- Historical days changed from 7-90 to 1-7 days
- Price filtering changed from single threshold (> X) to price range (X_min < price < X_max)
- EV calculation uses actual average entry price from qualifying trades
- Win/loss determination now uses `outcome_price` column from metadata (actual settlement value) instead of last trade price

## Parameters
- N: Number of historical days to analyze (1-7 days, default 7)
- X_min: Minimum price threshold (default 0.98)
- X_max: Maximum price threshold (default 1.00)
- Y: Minutes before resolution (default 2)

## Strategy
Find markets where the price Y minutes before resolution was in range [X_min, X_max], then check if the final price stayed above X_min (meaning the bet would win). Calculate EV using the actual average entry price.
