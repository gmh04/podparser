import psycopg2
import sys


class PodConnection(object):
    """
    Post Office Directory database connection.

    Currently only supports Postgis using the psycopg2 driver.
    """

    def __init__(self,
                 db_password,
                 db_name='ahistory',
                 db_user='ahistory',
                 db_host='localhost',
                 db_port=5432):
        """
        Constructor

        db_password - database password, the only mandatory field
        db_name     - database name (default ahistory)
        db_user     - database user name (default ahistory)
        db_host     - database hostname(default localhost)
        db_port     - database port(default 5432)
        """

        try:
            self.conn = psycopg2.connect(database=db_name,
                                         user=db_user,
                                         password=db_password,
                                         host=db_host,
                                         port=db_port)

        except psycopg2.OperationalError as e:
            print 'Failed to create DB connection %s' % e
            sys.exit(1)

    def set_directory(self, directory, commit=False):
        """
        Set directory to use for following commits.

        directory -- POD directory object.
        """
        self.pod_id = self._fetch_pod_id(directory)

        if not self.pod_id and commit:
            cur = self.conn.cursor()
            sql = """
                  INSERT INTO directory(country, town, year)
                  VALUES (%s, %s, %s) RETURNING id
                  """
            data = (directory.country, directory.town, directory.year)
            cur.execute(sql, data)
            self.conn.commit()
            self.pod_id = cur.fetchone()[0]

    def commit(self, page):
        """
        Commit a page and its contents to the database.

        page -- POD directory page object.
        """
        page_id = self._fetch_page_id(page)
        cur = self.conn.cursor()

        if not page_id:
            # no page exists insert it
            sql = """
                  INSERT INTO page(directory, section, number)
                  VALUES (%s, %s, %s) RETURNING id
                  """
            data = (self.pod_id, page.section, page.number)
            cur.execute(sql, data)

            # get the id of the page inserted above
            page_id = cur.fetchone()[0]

        for entry in page.entries:
            # insert entry
            sql = """
                  INSERT INTO entry(page, line)
                  VALUES (%s, %s) RETURNING id
                  """
            data = (page_id,
                    entry.line)
            cur.execute(sql, data)

            # get the id of the entry inserted above
            entry_id = cur.fetchone()[0]

            # insert entry details
            USER = 'parser'
            sql = """
                  INSERT INTO entry_detail(entry_id, surname, forename,
                                           profession, profession_category,
                                           address, userid_mod, current)
                  VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                  """
            data = (entry_id,
                    entry.surname,
                    entry.forename,
                    entry.profession,
                    entry.category,
                    entry.address,
                    USER,
                    'y')
            #print sql, data
            cur.execute(sql, data)

            for location in entry.locations:
                # insert each location for a given entry
                sql = """
                      INSERT INTO location(entry_id, address, accuracy, type,
                                           userid_mod, current, geom, exact,
                                           position)
                         VALUES (%s, %s,
                                 (SELECT id
                                  FROM location_accuracy where name = %s),
                                 %s, %s, %s,
                                 ST_GeomFromText('POINT(%s %s)', 4326), %s, %s)
                      """
                data = (entry_id,
                        location.address,
                        location.accuracy,
                        location.type,
                        USER,
                        True,
                        location.point['lng'],
                        location.point['lat'],
                        location.exact,

                        # position is the index of the location plus 1
                        entry.locations.index(location) + 1)
                cur.execute(sql, data)

        self.conn.commit()

    def record_google_lookup(self):
        """
        Increment the google premium lookup count.
        """
        cur = self.conn.cursor()
        cur.execute("""SELECT nextval('google_lookup_count')""")

    def _delete_directory(self, directory):
        # delete directory from db
        if directory:
            id = self._fetch_pod_id(directory)
            data = (id,)

            cur = self.conn.cursor()
            sql = """DELETE FROM directory CASCADE WHERE id = %s"""
            cur.execute(sql, data)
            self.conn.commit()

    def _fetch_page_id(self, page):
        # fetch page id for a given page object
        cur = self.conn.cursor()
        sql = "SELECT id FROM page WHERE directory = %s AND number = %s"
        data = (self.pod_id, page.number)
        return self._fetch_id(sql, data)

    def _fetch_pod_id(self, directory):
        # fetch POD id for a given directory object
        sql = """
              SELECT id
              FROM directory
              WHERE country = %s AND town = %s AND year = %s
              """
        data = (directory.country, directory.town, directory.year)
        return self._fetch_id(sql, data)

    def _fetch_id(self, sql, data):
        # fetch helper function
        id = None
        cur = self.conn.cursor()
        cur.execute(sql, data)
        row = cur.fetchone()
        if row:
            id = row[0]

        return id
