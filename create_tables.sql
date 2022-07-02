
CREATE TABLE IF NOT EXISTS quotes (
  SYMBOL char(20) NOT NULL,
  TIME timestamp NOT NULL,
  OMDSEQ bigint NOT NULL,
  ASK_SIZE double precision,
  ASK_PRICE double precision,
  BID_SIZE double precision,
  BID_PRICE double precision,
  PRIMARY KEY (TIME, OMDSEQ, SYMBOL)
);

CREATE TABLE IF NOT EXISTS trades (
  SYMBOL char(20) NOT NULL,
  TIME timestamp NOT NULL,
  OMDSEQ bigint NOT NULL,
  SIZE double precision,
  PRICE double precision,
  PRIMARY KEY (TIME, OMDSEQ, SYMBOL)
);
