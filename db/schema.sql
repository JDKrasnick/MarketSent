/*
 The sql table creation for my database. Will contain all posts along with the comments linking to the posts
 */

DROP TABLE IF EXISTS posts;

CREATE TABLE IF NOT EXISTS posts(
    postId    SERIAL PRIMARY KEY,
    text      TEXT,
    ticker    varchar(10),
    sentiment varchar(10),
    score     FLOAT,
    upvote_ratio FLOAT,
    creation  DATE,
    UNIQUE (text) -- I don't want to add duplicates, may happen if I get the same weeks for example
);

CREATE TABLE IF NOT EXISTS comments(
    commentId    SERIAL PRIMARY KEY,
    postID       INT,
    text         TEXT,
    sentiment    varchar(10),
    score        FLOAT,
    creation     DATE,
    UNIQUE (text, creation) -- Same logic as above
);


-- Some indexes for characteristics I'll want to lookup
CREATE INDEX post_day_created ON posts(creation);
CREATE INDEX ticker_type ON posts USING btree (ticker);
CREATE INDEX post_index_of_comment ON comments(postID);
