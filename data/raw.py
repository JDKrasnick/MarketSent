import psycopg2

CLIENT_ID = 'bkdE9Ydi0PcMTIeNPT_pMQ'


conn = psycopg2.connect(host="localhost", dbname = "postgres", user = "postgres", password = "ils&s!poJke5", port = "5432")


cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS post(
    id SERIAL PRIMARY KEY,
    text TEXT,
    ticker varchar(10),
    sentiment varchar(10),
    score FLOAT,
    creation DATE
);
""")

    
cur.execute("""SELECT * FROM post where SCORE > 1;""")

print(cur.fetchall())


conn.commit()
cur.close()
conn.close()