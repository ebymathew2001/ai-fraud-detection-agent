"""
db/init_db.py
=============
RUN THIS FIRST:  python db/init_db.py

Creates fraud.db with 3 tables:
  - customers
  - transactions  (normal + suspicious)
  - investigations (starts empty, populated by agent)
"""

import sqlite3

from config import DATABASE_URL





def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_URL)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables(conn: sqlite3.Connection):
    cursor = conn.cursor()

    # --- customers table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            home_city   TEXT NOT NULL
        )
    """)

    # --- transactions table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            txn_id               TEXT PRIMARY KEY,
            customer_id          TEXT NOT NULL,
            amount               REAL NOT NULL,
            merchant_name        TEXT NOT NULL,
            merchant_category    TEXT NOT NULL,
            transaction_location TEXT NOT NULL,
            timestamp            TEXT NOT NULL,
            status               TEXT NOT NULL CHECK(status IN ('NORMAL','SUSPICIOUS')),
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        )
    """)

    # --- investigations table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investigations (
            investigation_id TEXT PRIMARY KEY,
            txn_id           TEXT NOT NULL UNIQUE,
            risk_score       INTEGER NOT NULL,
            risk_level       TEXT NOT NULL,
            recommendation   TEXT NOT NULL,
            reasons          TEXT NOT NULL,   -- JSON array stored as string
            report           TEXT NOT NULL,   -- full report JSON blob
            created_at       TEXT NOT NULL,
            FOREIGN KEY (txn_id) REFERENCES transactions(txn_id)
        )
    """)

    conn.commit()
    print(" Tables created successfully.")


def seed_customers(conn: sqlite3.Connection):
    cursor = conn.cursor()
    customers = [
        ("CUST001", "Rahul Sharma", "Mumbai"),
        ("CUST002", "Priya Nair",   "Chennai"),
        ("CUST003", "Arjun Mehta",  "Delhi"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO customers (customer_id, name, home_city) VALUES (?, ?, ?)",
        customers
    )
    conn.commit()
    print(f" Seeded {len(customers)} customers.")


def seed_transactions(conn: sqlite3.Connection):
    cursor = conn.cursor()

    # ──────────────────────────────────────────────────────────────
    # RAHUL SHARMA (CUST001) — Mumbai-based, avg spend ~5300
    # ──────────────────────────────────────────────────────────────
    cust001_normal = [
        ("TXN001", "CUST001", 4500,  "Big Bazaar",        "GROCERIES",    "Mumbai",    "2025-05-01T10:00:00", "NORMAL"),
        ("TXN002", "CUST001", 6200,  "Reliance Digital",  "ELECTRONICS",  "Mumbai",    "2025-05-03T14:30:00", "NORMAL"),
        ("TXN004", "CUST001", 3800,  "Swiggy",            "FOOD",         "Mumbai",    "2025-05-05T19:00:00", "NORMAL"),
        ("TXN005", "CUST001", 7500,  "Shoppers Stop",     "CLOTHING",     "Mumbai",    "2025-05-07T12:00:00", "NORMAL"),
        ("TXN006", "CUST001", 2100,  "DMart",             "GROCERIES",    "Mumbai",    "2025-05-09T09:30:00", "NORMAL"),
        ("TXN007", "CUST001", 5500,  "IRCTC",             "TRAVEL",       "Mumbai",    "2025-05-11T08:00:00", "NORMAL"),
        ("TXN008", "CUST001", 4200,  "BookMyShow",        "ENTERTAINMENT","Mumbai",    "2025-05-13T16:00:00", "NORMAL"),
        ("TXN009", "CUST001", 8900,  "Croma",             "ELECTRONICS",  "Pune",      "2025-05-15T11:00:00", "NORMAL"),
        ("TXN010", "CUST001", 3100,  "Zomato",            "FOOD",         "Mumbai",    "2025-05-17T20:00:00", "NORMAL"),
        ("TXN011", "CUST001", 6000,  "Lifestyle",         "CLOTHING",     "Mumbai",    "2025-05-19T13:00:00", "NORMAL"),
        ("TXN012", "CUST001", 4800,  "Big Bazaar",        "GROCERIES",    "Mumbai",    "2025-05-21T10:30:00", "NORMAL"),
        ("TXN013", "CUST001", 5200,  "Flipkart",          "ELECTRONICS",  "Mumbai",    "2025-05-23T15:00:00", "NORMAL"),
        ("TXN014", "CUST001", 3600,  "Swiggy",            "FOOD",         "Pune",      "2025-05-25T19:30:00", "NORMAL"),
        ("TXN015", "CUST001", 7200,  "Tanishq",           "JEWELRY",      "Mumbai",    "2025-05-27T14:00:00", "NORMAL"),
        ("TXN016", "CUST001", 4100,  "More Supermarket",  "GROCERIES",    "Mumbai",    "2025-05-29T09:00:00", "NORMAL"),
        ("TXN017", "CUST001", 6800,  "MakeMyTrip",        "TRAVEL",       "Mumbai",    "2025-05-31T10:00:00", "NORMAL"),
        ("TXN018", "CUST001", 2900,  "Zomato",            "FOOD",         "Mumbai",    "2025-06-01T13:00:00", "NORMAL"),
        ("TXN019", "CUST001", 5800,  "Amazon",            "ELECTRONICS",  "Mumbai",    "2025-06-03T16:00:00", "NORMAL"),
        ("TXN020", "CUST001", 4400,  "Big Bazaar",        "GROCERIES",    "Mumbai",    "2025-06-05T11:00:00", "NORMAL"),
    ]

    # SUSPICIOUS for CUST001
    cust001_suspicious = [
        ("TXN003", "CUST001", 75000, "Al Jazeera Jewellers", "JEWELRY", "Dubai", "2025-06-07T03:00:00", "SUSPICIOUS"),
    ]

    # ──────────────────────────────────────────────────────────────
    # PRIYA NAIR (CUST002) — Chennai-based, avg spend ~4800
    # ──────────────────────────────────────────────────────────────
    cust002_normal = [
        ("TXN022", "CUST002", 3900,  "Saravana Stores",   "CLOTHING",     "Chennai",   "2025-05-01T10:00:00", "NORMAL"),
        ("TXN023", "CUST002", 5500,  "Poorvika Mobiles",  "ELECTRONICS",  "Chennai",   "2025-05-03T14:00:00", "NORMAL"),
        ("TXN024", "CUST002", 2800,  "Swiggy",            "FOOD",         "Chennai",   "2025-05-05T19:00:00", "NORMAL"),
        ("TXN025", "CUST002", 6200,  "Nalli Silks",       "CLOTHING",     "Chennai",   "2025-05-07T11:00:00", "NORMAL"),
        ("TXN026", "CUST002", 4100,  "Spencer's",         "GROCERIES",    "Chennai",   "2025-05-09T09:00:00", "NORMAL"),
        ("TXN027", "CUST002", 7800,  "IRCTC",             "TRAVEL",       "Chennai",   "2025-05-11T08:00:00", "NORMAL"),
        ("TXN028", "CUST002", 3400,  "Zomato",            "FOOD",         "Chennai",   "2025-05-13T20:00:00", "NORMAL"),
        ("TXN029", "CUST002", 5900,  "Croma",             "ELECTRONICS",  "Bangalore", "2025-05-15T12:00:00", "NORMAL"),
        ("TXN030", "CUST002", 4600,  "Big Bazaar",        "GROCERIES",    "Chennai",   "2025-05-17T10:30:00", "NORMAL"),
        ("TXN031", "CUST002", 6100,  "Lifestyle",         "CLOTHING",     "Chennai",   "2025-05-19T13:00:00", "NORMAL"),
        ("TXN032", "CUST002", 3200,  "Swiggy",            "FOOD",         "Chennai",   "2025-05-21T19:30:00", "NORMAL"),
        ("TXN033", "CUST002", 5400,  "Amazon",            "ELECTRONICS",  "Chennai",   "2025-05-23T15:00:00", "NORMAL"),
        ("TXN034", "CUST002", 4800,  "More Supermarket",  "GROCERIES",    "Chennai",   "2025-05-25T09:30:00", "NORMAL"),
        ("TXN035", "CUST002", 7200,  "MakeMyTrip",        "TRAVEL",       "Chennai",   "2025-05-27T10:00:00", "NORMAL"),
        ("TXN036", "CUST002", 2600,  "Zomato",            "FOOD",         "Bangalore", "2025-05-29T19:00:00", "NORMAL"),
        ("TXN037", "CUST002", 6800,  "Flipkart",          "ELECTRONICS",  "Chennai",   "2025-05-31T14:00:00", "NORMAL"),
        ("TXN038", "CUST002", 3800,  "Spencer's",         "GROCERIES",    "Chennai",   "2025-06-01T11:00:00", "NORMAL"),
        ("TXN039", "CUST002", 5100,  "BookMyShow",        "ENTERTAINMENT","Chennai",   "2025-06-03T16:00:00", "NORMAL"),
        ("TXN040", "CUST002", 4300,  "Saravana Stores",   "CLOTHING",     "Chennai",   "2025-06-05T12:00:00", "NORMAL"),
    ]

    # SUSPICIOUS for CUST002
    cust002_suspicious = [
        ("TXN021", "CUST002", 90000, "CryptoXchange", "CRYPTO", "Singapore", "2025-06-07T02:00:00", "SUSPICIOUS"),
    ]

    # ──────────────────────────────────────────────────────────────
    # ARJUN MEHTA (CUST003) — Delhi-based, avg spend ~6100
    # ──────────────────────────────────────────────────────────────
    cust003_normal = [
        ("TXN048", "CUST003", 5200,  "Lajpat Nagar Market","CLOTHING",    "Delhi",     "2025-05-01T10:00:00", "NORMAL"),
        ("TXN049", "CUST003", 7800,  "Croma",             "ELECTRONICS",  "Delhi",     "2025-05-03T14:00:00", "NORMAL"),
        ("TXN050", "CUST003", 3500,  "Swiggy",            "FOOD",         "Delhi",     "2025-05-05T19:00:00", "NORMAL"),
        ("TXN051", "CUST003", 9200,  "Tanishq",           "JEWELRY",      "Delhi",     "2025-05-07T13:00:00", "NORMAL"),
        ("TXN052", "CUST003", 4400,  "Big Bazaar",        "GROCERIES",    "Delhi",     "2025-05-09T10:00:00", "NORMAL"),
        ("TXN053", "CUST003", 8100,  "IRCTC",             "TRAVEL",       "Delhi",     "2025-05-11T09:00:00", "NORMAL"),
        ("TXN054", "CUST003", 3900,  "Zomato",            "FOOD",         "Delhi",     "2025-05-13T20:00:00", "NORMAL"),
        ("TXN055", "CUST003", 6700,  "Samsung Store",     "ELECTRONICS",  "Noida",     "2025-05-15T12:00:00", "NORMAL"),
        ("TXN056", "CUST003", 5100,  "DMart",             "GROCERIES",    "Delhi",     "2025-05-17T11:00:00", "NORMAL"),
        ("TXN057", "CUST003", 7400,  "Manyavar",          "CLOTHING",     "Delhi",     "2025-05-19T14:00:00", "NORMAL"),
        ("TXN058", "CUST003", 4200,  "Zomato",            "FOOD",         "Noida",     "2025-05-21T19:30:00", "NORMAL"),
        ("TXN059", "CUST003", 6500,  "Flipkart",          "ELECTRONICS",  "Delhi",     "2025-05-23T15:00:00", "NORMAL"),
        ("TXN060", "CUST003", 4900,  "Big Bazaar",        "GROCERIES",    "Delhi",     "2025-05-25T10:30:00", "NORMAL"),
        ("TXN061", "CUST003", 8800,  "MakeMyTrip",        "TRAVEL",       "Delhi",     "2025-05-27T08:00:00", "NORMAL"),
        ("TXN062", "CUST003", 3300,  "Swiggy",            "FOOD",         "Delhi",     "2025-05-29T19:00:00", "NORMAL"),
        ("TXN063", "CUST003", 7100,  "Amazon",            "ELECTRONICS",  "Delhi",     "2025-05-31T14:00:00", "NORMAL"),
        ("TXN064", "CUST003", 4600,  "Spencer's",         "GROCERIES",    "Delhi",     "2025-06-01T11:00:00", "NORMAL"),
        ("TXN065", "CUST003", 5800,  "BookMyShow",        "ENTERTAINMENT","Delhi",     "2025-06-03T16:00:00", "NORMAL"),
        ("TXN066", "CUST003", 6300,  "Manyavar",          "CLOTHING",     "Delhi",     "2025-06-05T13:00:00", "NORMAL"),
    ]

    # SUSPICIOUS for CUST003
    cust003_suspicious = [
        ("TXN047", "CUST003", 120000, "Tech Galaxy", "ELECTRONICS", "Hong Kong", "2025-06-07T01:00:00", "SUSPICIOUS"),
    ]
    
    # ── Extra suspicious transactions (MEDIUM / HIGH / LOW bands) ──
    extra_suspicious = [
        # MEDIUM ~40 — 2.3x avg, known city Mumbai, GIFT_CARDS high risk
        ("TXN101", "CUST001", 12000, "PayTM Wallet",  "GIFT_CARDS",   "Mumbai",    "2025-06-08T10:00:00", "SUSPICIOUS"),
        # MEDIUM ~45 — 3.8x avg, nearby region Bangalore, FOREX high risk
        ("TXN102", "CUST002", 18000, "FX Direct",     "FOREX",        "Bangalore", "2025-06-08T11:00:00", "SUSPICIOUS"),
        # HIGH ~60 — 7.4x avg, novel Indian city Kolkata, GIFT_CARDS high risk
        ("TXN103", "CUST003", 45000, "GiftCard Hub",  "GIFT_CARDS",   "Kolkata",   "2025-06-08T12:00:00", "SUSPICIOUS"),
        # HIGH ~65 — 7.2x avg, novel Indian city Hyderabad, WIRE_TRANSFER high risk
        ("TXN104", "CUST001", 38000, "Wire Express",  "WIRE_TRANSFER","Hyderabad", "2025-06-08T13:00:00", "SUSPICIOUS"),
        # LOW ~25 — 2x avg, known city Chennai, CLOTHING normal category
        ("TXN105", "CUST002", 9500,  "Lifestyle",     "CLOTHING",     "Chennai",   "2025-06-08T14:00:00", "SUSPICIOUS"),
    ]


    all_txns = (
        cust001_normal + cust001_suspicious +
        cust002_normal + cust002_suspicious +
        cust003_normal + cust003_suspicious + 
        extra_suspicious
       
    )

    cursor.executemany(
        """INSERT OR IGNORE INTO transactions
           (txn_id, customer_id, amount, merchant_name, merchant_category,
            transaction_location, timestamp, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        all_txns
    )
    conn.commit()
    print(f" Seeded {len(all_txns)} transactions ({len(all_txns) - 3} NORMAL, 3 SUSPICIOUS).")


def main():
    print("Initializing fraud.db ...")
    conn = get_connection()
    create_tables(conn)
    seed_customers(conn)
    seed_transactions(conn)
    conn.close()
    print(" Database ready at:", DATABASE_URL)


if __name__ == "__main__":
    main()