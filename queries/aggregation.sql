SELECT 
    symbol, AVG(price) AS average_price
FROM 
    trades
GROUP BY
	symbol;

SELECT 
    symbol, AVG((ask_price + bid_price)/2) AS mid_price
FROM 
    quotes
GROUP BY
    symbol;