import sqlite3

class Database:

    path = None
    cur = None

    def __init__(self, path):
        self.path = path
        self.cur = self.connect_to_db()
        self.maybe_create_tables(self.cur)

    def connect_to_db(self):
        con = sqlite3.connect(self.path)
        cur = con.cursor()
        return cur

    def maybe_create_tables(self, cur):
        cur.execute("CREATE TABLE IF NOT EXISTS sitemap_url (url TEXT UNIQUE, success INTEGER)")
        cur.execute("CREATE TABLE IF NOT EXISTS package_name (package_name TEXT UNIQUE)")
        cur.execute("CREATE TABLE IF NOT EXISTS info (package_name TEXT UNIQUE, free INTEGER, min_installs INTEGER, icon TEXT, json TEXT, permissions TEXT, success INTEGER)")
        cur.execute("CREATE TABLE IF NOT EXISTS icon (package_name TEXT UNIQUE, success INTEGER)")

    def add_package_name_info(self, package_name, free, min_installs, icon, json, permissions, success=1):
        self.cur.execute("INSERT INTO info (package_name, free, min_installs, icon, json, success, permissions) VALUES (?, ?, ?, ?, ?, ?, ?)", (package_name, free, min_installs, icon, str(json), str(permissions), success))
        self.cur.connection.commit()

    def insert_sitemap_urls(self, urls):
        data = [(url, 0) for url in urls]
        try:
            self.cur.executemany("INSERT INTO sitemap_url (url, success) VALUES (?, ?)", data)
            self.cur.connection.commit()
        except sqlite3.IntegrityError:
            pass

    def get_unsuccessful_sitemap_urls(self):
        self.cur.execute("SELECT url FROM sitemap_url WHERE success = 0")
        results = self.cur.fetchall()
        return [result[0] for result in results]
    
    def get_package_names(self):
        self.cur.execute("SELECT package_name FROM package_name")
        results = self.cur.fetchall()
        return [result[0] for result in results]
    
    def get_package_name_info_to_fetch(self):
        self.cur.execute("SELECT package_name FROM package_name WHERE package_name NOT IN (SELECT package_name FROM info WHERE success = 1 OR success = 404)")
        results = self.cur.fetchall()
        return [result[0] for result in results]

    def get_sitemap_urls(self):
        self.cur.execute("SELECT url FROM sitemap_url")
        results = self.cur.fetchall()
        return [result[0] for result in results]

    def add_success_package_names(self, xml_url, package_names):
        self.cur.execute("INSERT OR REPLACE INTO sitemap_url (url, success) VALUES (?, 1)", (xml_url,))
        for package_name in package_names:
            self.cur.execute("INSERT OR REPLACE INTO package_name (package_name) VALUES (?)", (package_name,))
        self.cur.connection.commit()

    def get_missing_icon_urls(self):
        self.cur.execute("SELECT package_name, icon FROM info WHERE icon IS NOT NULL AND package_name NOT IN (SELECT package_name FROM icon WHERE success = 1)")
        results = self.cur.fetchall()
        return results
    
    def set_icon_status(self, package_name, success):
        self.cur.execute("INSERT OR REPLACE INTO icon (package_name, success) VALUES (?, ?)", (package_name, success))
        self.cur.connection.commit()

    def close(self):
        self.cur.connection.close()

