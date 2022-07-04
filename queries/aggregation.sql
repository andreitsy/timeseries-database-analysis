SELECT 
    AVG(price) AS total
FROM 
    trades
GROUP BY
	symbol;