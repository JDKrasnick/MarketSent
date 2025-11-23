/*
 The sql table creation for my database. Will contain all posts along with the comments linking to the posts
 */

DROP TABLE IF EXISTS posts;

CREATE TABLE IF NOT EXISTS posts(
    postId    SERIAL PRIMARY KEY,
    text      TEXT,
    tickers   TEXT,
    positive DOUBLE PRECISION,
    negative DOUBLE PRECISION,
    neutral DOUBLE PRECISION,
    post_text TEXT,
    score     FLOAT,
    upvote_ratio FLOAT,
    creation  DATE,
    UNIQUE (text) -- I don't want to add duplicates, may happen if I get the same weeks for example
);



-- Some indexes for characteristics I'll want to lookup
CREATE INDEX post_day_created ON posts(creation);
CREATE INDEX post_index_of_comment ON comments(postID);
