// price aggregate
from(bucket:"quotes_trades")
    |> range(start: 0, stop: now())
    |> filter(fn: (r) => r._measurement == "trades" and r._field == "price")
    |> mean()
    |> yield()

// mid price aggregate
ask_stream = from(bucket:"quotes_trades")
    |> range(start: 0, stop: now())
    |> filter(fn: (r) => r._measurement == "quotes" and r._field == "ask_price")
    |> mean()

bid_stream = from(bucket:"quotes_trades")
    |> range(start: 0, stop: now())
    |> filter(fn: (r) => r._measurement == "quotes" and r._field == "bid_price")
    |> mean()

join(tables: {ask: ask_stream, bid: bid_stream}, on: ["symbol"])
    |> map(fn: (r) => ({symbol: r.symbol, _time: r._time, 
                        mid_price: (r._value_ask + r._value_bid) / 2.0}))
    |> yield()
