import pymysql
conn = pymysql.connect(host='127.0.0.1', port=3307, user='root', password='Jace102020.', autocommit=True)
with conn.cursor() as cur:
    cur.execute("CREATE DATABASE IF NOT EXISTS `helpticket_system` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")
conn.close()
print('Database created (or already exists).')