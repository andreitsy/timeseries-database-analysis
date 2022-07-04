
CREATE TABLE IF NOT EXISTS quotes (
  SYMBOL char(20) NOT NULL,
  TIME timestamp NOT NULL,
  OMDSEQ bigint NOT NULL,
  ASK_SIZE double precision,
  ASK_PRICE double precision,
  BID_SIZE double precision,
  BID_PRICE double precision,
  PRIMARY KEY (SYMBOL, TIME, OMDSEQ)
);

CREATE TABLE IF NOT EXISTS trades (
  SYMBOL char(20) NOT NULL,
  TIME timestamp NOT NULL,
  OMDSEQ bigint NOT NULL,
  SIZE double precision,
  PRICE double precision,
  PRIMARY KEY (SYMBOL, TIME, OMDSEQ)
);

CREATE INDEX idx_trades ON trades(SYMBOL);
CREATE INDEX idx_quotes ON quotes(SYMBOL);