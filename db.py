import psycopg2
from psycopg2.extras import RealDictCursor

db = psycopg2.connect()
cur = db.cursor(cursor_factory=RealDictCursor)

cur.execute("""
    CREATE TABLE IF NOT EXISTS leases (
        first_seen integer,
        last_seen  integer,
        ip   text,
        mac  text,
        port text,
        sw   text
    )""")

def insert_new_lease(identity, time):
    query_insert_new = """
        INSERT INTO leases(first_seen, last_seen, ip, mac, sw, port)
        VALUES (%(first_seen)s, %(last_seen)s, %(ip)s, %(mac)s, %(sw)s, %(port)s)
    """
    cur.execute(query_insert_new, identity | {"first_seen": time, "last_seen": time})


def update_lease(identity, first_seen, time):
    query_update = """
    UPDATE leases
    SET last_seen = %(time)s
    WHERE 
        ip = %(ip)s AND mac = %(mac)s AND
        port = %(port)s AND sw = %(sw)s AND
        first_seen = %(first_seen)s
    """
    cur.execute(query_update, identity | { "first_seen": first_seen, "time": time })


def find_last(ip):
    query_find_last = """
        SELECT * FROM leases
        WHERE ip=%(ip)s
        ORDER BY last_seen DESC
        LIMIT 1
    """
    cur.execute(query_find_last, {"ip": ip})
    return cur.fetchone()


def register_lease(ip, mac, sw, port, time):
    identity = { "ip": ip, "mac": mac, "sw": sw, "port": port }
    old = find_last(ip)

    if old:
        old_id = {
            'ip': old['ip'], 'mac': old['mac'],
            'port': old['port'], 'sw': old['sw'],
        }
        if identity == old_id:
            print(f'Renewed IP: {ip}')
            update_lease(identity, old['first_seen'], time)
        else:
            print(f'Moved IP: {ip}')
            insert_new_lease(identity, time)
    else:
        print(f'New IP: {ip}')
        insert_new_lease(identity, time)
    db.commit()

def get_history(ip, limit=None):
    query = """
    SELECT * FROM leases
    WHERE ip=%(ip)s
    ORDER BY last_seen DESC
    """
    if limit:
        query += f" LIMIT %(limit)s"
    cur.execute(query, {"ip": ip, "limit": limit})
    return cur.fetchall()


