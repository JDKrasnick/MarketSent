import psycopg2

conn = psycopg2.connect(host="localhost", dbname = "postgres", user = "postgres", password = "ils&s!poJke5", port = "5432")


cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXIST")

conn.commit()
cur.close()
conn.close()