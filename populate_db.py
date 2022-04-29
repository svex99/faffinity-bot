import sqlite3

import edgedb


sql3_con = sqlite3.connect("faffinity-bot.session")
edgedb_client = edgedb.create_client()

cur = sql3_con.cursor()
for row in cur.execute("SELECT id FROM entities"):
    edgedb_client.query(
        'INSERT User {tid := <int64>$tid, lang := <str>$lang}',
        tid=row[0], lang='es'
    )

sql3_con.close()
edgedb_client.close()
