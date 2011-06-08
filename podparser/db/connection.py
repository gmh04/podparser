import psycopg2
import sys

class PodConnection(object):
    """
    Post Office Directory database connection.

    Currently only supports Postgis using the psycopg2 driver.
    """

    def __init__(self,
                 db_password,
                 db_name     = 'ahistory',
                 db_user     = 'ahistory',
                 db_host     = 'localhost',
                 db_port     = 5432):
        """
        Constructor

        db_password -- database password, the only mandatory field
        db_name     -- database name (default ahistory)
        db_user     -- database user name (default ahistory)
        db_host     -- database hostname(default localhost)
        db_port     -- database port(default 5432)
        """

        try:
            self.conn = psycopg2.connect(database = db_name,
                                         user     = db_user,
                                         password = db_password,
                                         host     = db_host,
                                         port     = '5432')

        except psycopg2.OperationalError as e:
            print 'Failed to create DB connection %s' % e
            sys.exit(1)

    def set_directory(self, directory):

        self.pod_id = self._fetch_pod_id(directory)

        if not self.pod_id:
            cur = self.conn.cursor()
            sql = "INSERT INTO directory(country, town, year) VALUES (%s, %s, %s) RETURNING id";
            data = (directory.country, directory.town, directory.year)
            cur.execute(sql, data)
            self.conn.commit()
            self.pod_id = cur.fetchone()[0]

    def commit(self, page):
        page_id = self._fetch_page_id(page)

        if not page_id:
            cur = self.conn.cursor()
            sql = "INSERT INTO page(directory, section, number) VALUES (%s, %s, %s) RETURNING id";
            data = (self.pod_id, page.section, page.number)
            cur.execute(sql, data)
            self.conn.commit()
            page_id = cur.fetchone()[0]

        for entry in page.entries:
            cur = self.conn.cursor()
            sql = """INSERT INTO entry(page, surname, forename, profession, profession_category, address, line)
                     VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id"""
            data = (page_id,
                    entry.surname,
                    entry.forename,
                    entry.profession,
                    entry.category,
                    entry.address,
                    entry.line)

            cur.execute(sql, data)
            entry_id = cur.fetchone()[0]

            for location in entry.locations:
                print location.point
                sql = """INSERT INTO location(entry_id, address, accuracy, type, geom)
                         VALUES (%s, %s, %s, %s, ST_GeomFromText('POINT(%s %s)', 4326))"""
                data = (entry_id,
                        location.address,
                        1,
                        location.type,
                        location.point['lng'],
                        location.point['lat'])
                cur.execute(sql, data)

        self.conn.commit()

    def _fetch_entry_id(self, directory):
        sql = "SELECT id FROM entry WHERE country = %s AND town = %s AND year = %s"
        data = (directory.country, directory.town, directory.year)
        return self._fetch_id(sql, data)

    def _fetch_page_id(self, page):
        cur = self.conn.cursor()
        sql = "SELECT id FROM page WHERE directory = %s AND number = %s"
        data = (self.pod_id, page.number)
        return self._fetch_id(sql, data)

    def _fetch_pod_id(self, directory):
        sql = "SELECT id FROM directory WHERE country = %s AND town = %s AND year = %s"
        data = (directory.country, directory.town, directory.year)
        return self._fetch_id(sql, data)

    def _fetch_id(self, sql, data):
        id = None
        cur = self.conn.cursor()
        cur.execute(sql, data)
        row = cur.fetchone()
        if row:
            print row
            id = row[0]

        return id
