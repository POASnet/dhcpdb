
def get_version(cur):
    cur.execute("SELECT version from db_version")
    version = cur.fetchone()['version']
    print("DB: version = ", version)
    return version


def init(db, cur):
    init_v1(cur)

    if get_version(cur) < 2:
        upgrade_v2(cur)

    db.commit()


def init_v1(cur):
    #####################
    # Initial DB Schema #
    #####################
    print("DB: Initializing")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS leases (
            first_seen integer,
            last_seen  integer,
            ip   text,
            mac  text,
            port text,
            sw   text
    )""")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS db_version (
            version integer
    )""")

    cur.execute("""
        INSERT INTO db_version (version)
        SELECT '1'
        WHERE NOT EXISTS (SELECT * FROM db_version)
    """)


def upgrade_v2(cur):
    ##########################################################
    # Schema V2 to handle separate DISCOVER and ACK messages #
    ##########################################################
    print("DB: Upgrading schema to V2")

    cur.execute("""
        ALTER TABLE leases RENAME TO leases_old
    """)

    cur.execute("""
        CREATE TABLE clients (
            first_seen integer,
            last_seen  integer,
            mac  text,
            port text,
            sw   text
        )
    """)

    cur.execute("""
        INSERT INTO clients
        SELECT first_seen, last_seen, mac, port, sw
        FROM leases_old
    """)

    cur.execute("""
        CREATE TABLE leases (
            first_seen integer,
            last_seen  integer,
            lease_time integer,
            ip   text,
            mac  text
        )""")

    cur.execute("""
        INSERT INTO leases
        SELECT first_seen, last_seen, 0 as lease_time, ip, mac
        FROM leases_old
    """)

    cur.execute("DROP TABLE leases_old")
    cur.execute("UPDATE db_version SET version=2")

