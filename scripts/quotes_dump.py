# !/usr/bin/env python
import os
import gc
from pathlib import Path

import onetick.py as otp
import pandas as pd

if __name__ == "__main__":
    pattern = "%"
    for d in pd.date_range(start='2017-01-06', end='2017-01-07'):
        start=otp.datetime(d.year, d.month, d.day)
        end=otp.datetime(d.year, d.month, d.day, 23, 59, 59)
        tz = "EST5EDT"
        symbols = otp.run(otp.Symbols(db="NYSE_TAQ", pattern=pattern),
                          start=start, end=end, timezone=tz)
        for sn in symbols["SYMBOL_NAME"].to_list():
            src = otp.DataSource(db="NYSE_TAQ", tick_type="TRD")
            df = otp.run(src, symbols=sn, start=start, end=end, timezone=tz)
            path = (Path(os.path.dirname(os.path.realpath(__file__)))
                    / "dump" / f"{sn}_{d.year}_{d.month}_{d.day}_trd.csv")
            if not df.empty:
                df["SYMBOL"] = sn
                df[["SYMBOL", "Time", "OMDSEQ", "SIZE", "PRICE"]].to_csv(
                    path, index=False)

            src = otp.DataSource(db="NYSE_TAQ", tick_type="QTE")
            df = otp.run(src, symbols=sn, start=start, end=end, timezone=tz)
            path = (Path(os.path.dirname(os.path.realpath(__file__)))
                    / "dump" / f"{sn}_{d.year}_{d.month}_{d.day}_qte.csv")
            if not df.empty:
                df["SYMBOL"] = sn
                df[["SYMBOL", "Time", "OMDSEQ", "ASK_SIZE",
                    "ASK_PRICE", "BID_SIZE", "BID_PRICE"]].to_csv(
                    path, index=False)

            df = None
            gc.collect()
