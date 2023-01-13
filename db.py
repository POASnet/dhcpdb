import psycopg2
from psycopg2.extras import RealDictCursor

import db_schema

db = psycopg2.connect()
cur = db.cursor(cursor_factory=RealDictCursor)
db_schema.init(db, cur)


def extract(object, keys):
    result = {}
    for key in keys:
        result[key] = object[key]
    return result


def insert_new_client(identity, time):
    query_insert_new = """
        INSERT INTO clients(first_seen, last_seen, mac, sw, port)
        VALUES (%(first_seen)s, %(last_seen)s, %(mac)s, %(sw)s, %(port)s)
    """
    cur.execute(query_insert_new, identity | {"first_seen": time, "last_seen": time})


def update_client(identity, first_seen, last_seen):
    query_update = """
    UPDATE clients
    SET last_seen = %(last_seen)s
    WHERE 
        mac = %(mac)s AND sw = %(sw)s AND port = %(port)s AND
        first_seen = %(first_seen)s
    """
    cur.execute(query_update, identity | {"first_seen": first_seen, "last_seen": last_seen})


def insert_new_lease(identity, time, lease_time):
    query_insert_new = """
        INSERT INTO leases(first_seen, last_seen, ip, mac)
        VALUES (%(first_seen)s, %(last_seen)s, %(ip)s, %(mac)s)
    """
    cur.execute(query_insert_new, identity | {"first_seen": time, "last_seen": time, "lease_time": lease_time})


def update_lease(identity, first_seen, last_seen, lease_time):
    query_update = """
    UPDATE leases
    SET last_seen = %(last_seen)s, lease_time = %(lease_time)s
    WHERE 
        ip = %(ip)s AND mac = %(mac)s AND
        first_seen = %(first_seen)s
    """
    cur.execute(query_update, identity | {"first_seen": first_seen, "last_seen": last_seen, "lease_time": lease_time})


def find_last(table, key, value):
    q = f"""
        SELECT * FROM {table}
        WHERE {key} = %(value)s
        ORDER BY last_seen DESC
        LIMIT 1
    """
    cur.execute(q, {"value": value})
    return cur.fetchone()


def find_mac_last(mac):
    return find_last(table='clients', key='mac', value=mac)


def find_ip_last(ip):
    return find_last(table='leases', key='ip', value=ip)


def register_compat(ip, mac, sw, port, time, **kwargs):
    register_client(mac, sw, port, time)
    register_lease(ip, mac, time, 0)


def register_client(mac, sw, port, time_seen, **kwargs):
    identity = {"mac": mac, "sw": sw, "port": port}
    old = find_mac_last(mac)

    if old:
        if time_seen < old['last_seen']:
            print(f'Ignoring MAC: {mac} - newer timestamp exists')
            return
        old_id = extract(old, ['mac', 'sw', 'port'])
        if identity == old_id:
            print(f'Refreshing existing client: {mac}')
            update_client(identity, old['first_seen'], time_seen)
        else:
            print(f'Moved client: {mac}')
            insert_new_client(identity, time_seen)
    else:
        print(f'New client: {mac}')
        insert_new_client(identity, time_seen)
    db.commit()


def register_lease(ip, mac, time_seen, lease_time, **kwargs):
    identity = {"ip": ip, "mac": mac}
    old = find_ip_last(ip)

    if old:
        if time_seen < old['last_seen']:
            print(f'Ignoring IP: {ip} - newer timestamp exists')
            return
        old_id = extract(old, ['ip', 'mac'])
        if identity == old_id:
            print(f'Renewed IP: {ip}')
            update_lease(identity, old['first_seen'], time_seen, lease_time)
        else:
            print(f'Moved IP: {ip}')
            insert_new_lease(identity, time_seen, lease_time)
    else:
        print(f'New IP: {ip}')
        insert_new_lease(identity, time_seen, lease_time)
    db.commit()


def get_ip_history(ip, limit=None):
    result = []

    query = """
    SELECT * FROM leases
    WHERE ip=%(ip)s
    ORDER BY last_seen DESC
    """
    if limit:
        query += f" LIMIT %(limit)s"
    cur.execute(query, {"ip": ip, "limit": limit})
    leases = cur.fetchall()

    if not leases:
        return None

    for lease in leases:
        cur.execute("""
            SELECT * FROM clients
            WHERE mac=%(mac)s
            ORDER BY last_seen DESC
            LIMIT 1
        """, {"mac": lease['mac']})
        result.append((cur.fetchone() or {}) | lease)

    return result


def get_port_history(sw, port, limit=None):
    result = []

    query = """
    SELECT * FROM clients
    WHERE sw=%(sw)s AND port=%(port)s
    ORDER BY last_seen DESC
    """
    if limit:
        query += f" LIMIT %(limit)s"
    cur.execute(query, {"sw": sw.split('.')[0], "port": port, "limit": limit})
    clients = cur.fetchall()
    print(query, sw.split('.')[0], port)

    if not clients:
        return None

    for client in clients:
        # TODO: Get IP information
        result.append(client)

    return result
