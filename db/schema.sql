/*
 The sql table creation for my database. Will contain all posts along with the comments linking to the posts
 */


CREATE TABLE IF NOT EXISTS post(
    postId    SERIAL PRIMARY KEY,
    text      TEXT,
    ticker    varchar(10),
    sentiment varchar(10),
    score     FLOAT,
    creation  DATE
);

CREATE TABLE comments(
    commentId    SERIAL PRIMARY KEY,
    postID       INT,
    text         TEXT,
    sentiment    varchar(10),
    score        FLOAT,
    creation     DATE
);


-- Some indexes for characteristics I'll want to lookup
CREATE INDEX post_day_created ON post(creation);
CREATE INDEX ticker_type ON post USING GIN (ticker);
CREATE INDEX post_index_of_comment ON comments(postID);
