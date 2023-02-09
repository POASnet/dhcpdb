import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Optional

import db_schema

db = psycopg2.connect()
cur = db.cursor(cursor_factory=RealDictCursor)
db_schema.init(db, cur)


def extract(object, keys):
    result = {}
    for key in keys:
        result[key] = object[key]
    return result


def insert_new_client(identity, time) -> int:
    query_insert_new = """
        INSERT INTO clients(first_seen, last_seen, mac, sw, port)
        VALUES (%(first_seen)s, %(last_seen)s, %(mac)s, %(sw)s, %(port)s)
        RETURNING id
    """
    cur.execute(query_insert_new, identity | {"first_seen": time, "last_seen": time})
    return cur.fetchone()[0]


def update_client(client_id, last_seen):
    query_update = """
        UPDATE clients
        SET last_seen = %(last_seen)s
        WHERE id = %(id)s
    """
    cur.execute(query_update, {"id": client_id, "last_seen": last_seen})


def insert_new_lease(identity, time, lease_time):
    query_insert_new = """
        INSERT INTO leases(first_seen, last_seen, client, ip, mac)
        VALUES (%(first_seen)s, %(last_seen)s, %(client)s, %(ip)s, %(mac)s)
    """
    print(identity | {"first_seen": time, "last_seen": time, "lease_time": lease_time, "mac": '00:00:00:00:00:00'})
    cur.execute(
        query_insert_new,
        identity | {"first_seen": time, "last_seen": time, "lease_time": lease_time, "mac": '00:00:00:00:00:00'}
    )


def update_lease(identity, first_seen, last_seen, lease_time):
    query_update = """
    UPDATE leases
    SET last_seen = %(last_seen)s, lease_time = %(lease_time)s
    WHERE 
        ip = %(ip)s AND client = %(client)s AND
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


def find_mac_last(mac: str) -> dict:
    return find_last(table='clients', key='mac', value=mac)


def find_ip_last(ip: str) -> dict:
    return find_last(table='leases', key='ip', value=ip)


def register_client(mac, sw, port, time_seen, **kwargs) -> Optional[dict]:
    identity = {"mac": mac, "sw": sw, "port": port}
    old = find_mac_last(mac)

    if old:
        old_identity = extract(old, ['mac', 'sw', 'port'])
        if identity == old_identity:
            if time_seen < old['last_seen']:
                print(f'Ignoring MAC: {mac} - newer timestamp exists')
                return old
            else:
                print(f'Refreshing existing client: {mac}')
                client_id = old['id']
                update_client(client_id, time_seen)
        else:
            print(f'Moved client: {mac}')
            client_id = insert_new_client(identity, time_seen)
    else:
        print(f'New client: {mac}')
        client_id = insert_new_client(identity, time_seen)

    db.commit()
    cur.execute("SELECT * FROM clients WHERE id=%(id)s", {"id": client_id})
    return cur.fetchone()


def register_lease(ip, mac, time_seen, lease_time, sw, port, **kwargs):
    client = register_client(mac, sw, port, time_seen)
    identity = {"client": client['id'], "ip": ip}
    old = find_ip_last(ip)

    if old:
        old_id = extract(old, ['ip', 'client'])
        if identity == old_id:
            if time_seen < old['last_seen']:
                print(f'Ignoring IP: {ip} - newer timestamp exists')
                return
            else:
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
    query = """
    SELECT 
        leases.first_seen, leases.last_seen, leases.lease_time, leases.ip, 
        clients.mac, clients.sw, clients.port 
    FROM leases
    JOIN clients ON leases.client = clients.id
    WHERE ip=%(ip)s
    ORDER BY last_seen DESC
    """
    if limit:
        query += f" LIMIT %(limit)s"

    cur.execute(query, {"ip": ip, "limit": limit})
    return cur.fetchall()


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
