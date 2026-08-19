/*
 The sql table creation for my database. Will contain all posts along with the comments linking to the posts
 */

CREATE TABLE IF NOT EXISTS posts(
    postId    SERIAL PRIMARY KEY,
    text      TEXT,
    tickers   TEXT,
    positive DOUBLE PRECISION,
    negative DOUBLE PRECISION,
    neutral DOUBLE PRECISION,
    confidence FLOAT,
    post_text TEXT,
    score     FLOAT,
    upvote_ratio FLOAT,
    creation  DATE,
    UNIQUE (text) -- I don't want to add duplicates, may happen if I get the same weeks for example
);



-- Some indexes for characteristics I'll want to lookup
CREATE INDEX IF NOT EXISTS post_day_created ON posts(creation);
