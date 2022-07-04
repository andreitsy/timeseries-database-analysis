SELECT 
    trd.symbol as symbol, trd.time as trd_time, 
    qte.time as qte_time, trd.price, 
    qte.ask_price, qte.bid_price
FROM 
    trades as trd
JOIN
	quotes as qte 
ON trd.symbol = qte.symbol;