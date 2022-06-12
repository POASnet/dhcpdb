import sqlite3

db = sqlite3.connect('dhcp.db')
db.row_factory = sqlite3.Row
cur = db.cursor()

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
        VALUES (:first_seen, :last_seen, :ip, :mac, :sw, :port)
    """
    cur.execute(query_insert_new, identity | {"first_seen": time, "last_seen": time})


def update_lease(identity, first_seen, time):
    query_update = """
    UPDATE leases
    SET last_seen = :time
    WHERE 
        ip = :ip AND mac = :mac AND
        port = :port AND sw = :sw AND
        first_seen = :first_seen
    """
    cur.execute(query_update, identity | { "first_seen": first_seen, "time": time })


def find_last(ip):
    query_find_last = """
        SELECT * FROM leases
        WHERE ip=:ip
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


test = {'ip': '11.22.33.44', 'mac': '00:16:01:02:03:04', 'sw': 'test-sw1', 'port': 'gei-0/1/1/13', 'time': 1654727124}
register_lease(**test)
test['time'] += 1
register_lease(**test)
test['time'] += 1
test['port'] = 'gei-0/1/1/14'
register_lease(**test)
test['time'] += 1
register_lease(**test)


