// price aggregate
from(bucket:"quotes_trades")
    |> range(start: 0, stop: now())
    |> filter(fn: (r) => r._measurement == "trades" and r._field == "price")
    |> mean()
    |> yield()

// mid price aggregate
// - slow version:
from(bucket:"quotes_trades")
    |> range(start: 0, stop: now())
    |> filter(fn: (r) => r._measurement == "quotes" and
                         (r._field == "ask_price" or r._field == "bid_price"))                  
    |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
    |> map(fn: (r) => ({ r with _value: (r.ask_price + r.bid_price) / 2.0 }))
    |> mean()
    |> map(fn: (r) => ({ mid_price: r._value, symbol: r.symbol}))
// - fast version:
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
