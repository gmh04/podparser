DROP TABLE location;
DROP TABLE location_accuracy;
DROP TABLE entry;
DROP TABLE profession_category;
DROP TABLE page;
DROP TABLE directory;

CREATE TABLE directory (id      SERIAL PRIMARY KEY,
                        country text,
                        town    text,
                        year    integer,
                        UNIQUE (country, town, year)
);

CREATE TABLE page (id        SERIAL  PRIMARY KEY,
                   directory integer REFERENCES directory(id),
                   section   text,
                   number    integer,
                   UNIQUE (directory, number)
);

CREATE TABLE profession_category (code     char PRIMARY KEY,
                                  category text
);

CREATE TABLE entry (id                  SERIAL  PRIMARY KEY,
                    page                integer REFERENCES page(id),
                    surname             text,
                    forename            text,
                    profession          text,
                    profession_category char    REFERENCES profession_category(code),
                    address             text,
                    line                text
);

CREATE INDEX surname_idx    ON entry (surname);
CREATE INDEX forname_idx    ON entry (forename);
CREATE INDEX profession_idx ON entry (profession);

COMMENT ON COLUMN entry.address IS 'address as seen in POD';
COMMENT ON COLUMN entry.line    IS 'original line entry of text in djvu xml';

CREATE TABLE location_accuracy (id   integer PRIMARY KEY,
                                name text
);

CREATE TABLE location (entry_id  integer REFERENCES entry(id),
                       address   text,
                       accuracy  integer REFERENCES location_accuracy(id),
                       type      text
);
SELECT AddGeometryColumn('public', 'location', 'geom', 4326, 'POINT', 2);
CREATE INDEX location_idx ON location USING GIST (geom);

COMMENT ON COLUMN location.address IS 'address used in geo tagging';

INSERT INTO directory(country, town, year) VALUES ('Scotland', 'Edinburgh', 1784);
INSERT INTO directory(country, town, year) VALUES ('Scotland', 'Edinburgh', 1865);
INSERT INTO directory(country, town, year) VALUES ('Scotland', 'Edinburgh', 1905);

INSERT INTO profession_category (code, category) VALUES ('A', 'Agriculture, forestry and fishing');
INSERT INTO profession_category (code, category) VALUES ('B', 'Mining and quarrying');
INSERT INTO profession_category (code, category) VALUES ('C', 'Manufacturing');
INSERT INTO profession_category (code, category) VALUES ('D', 'Electricity, gas, steam and air conditioning supply');
INSERT INTO profession_category (code, category) VALUES ('E', 'Water supply; sewerage, waste management and remediation activities');
INSERT INTO profession_category (code, category) VALUES ('F', 'Construction');
INSERT INTO profession_category (code, category) VALUES ('G', 'Wholesale and retail trade; repair of motor vehicles and motor cycles');
INSERT INTO profession_category (code, category) VALUES ('H', 'Transport and storage');
INSERT INTO profession_category (code, category) VALUES ('I', 'Accommodation and food service activities');
INSERT INTO profession_category (code, category) VALUES ('J', 'Information and communication');
INSERT INTO profession_category (code, category) VALUES ('K', 'Financial and insurance activities');
INSERT INTO profession_category (code, category) VALUES ('L', 'Real estate activities');
INSERT INTO profession_category (code, category) VALUES ('M', 'Professional, scientific and technical activities');
INSERT INTO profession_category (code, category) VALUES ('N', 'Administrative and support service activities');
INSERT INTO profession_category (code, category) VALUES ('O', 'Public administration and defence; compulsory social security');
INSERT INTO profession_category (code, category) VALUES ('P', 'Education');
INSERT INTO profession_category (code, category) VALUES ('Q', 'Human health and social work activities');
INSERT INTO profession_category (code, category) VALUES ('R', 'Arts, entertainment and recreation');
INSERT INTO profession_category (code, category) VALUES ('S', 'Other service activities');
INSERT INTO profession_category (code, category) VALUES ('T', 'Activities of households as employers; undifferentiated goods-and services-producing activities of households for own use');
INSERT INTO profession_category (code, category) VALUES ('U', 'Activities of extraterritorial organisations and bodies');

INSERT INTO location_accuracy (id, name) VALUES (5, 'ROOFTOP');
INSERT INTO location_accuracy (id, name) VALUES (4, 'RANGE_INTERPOLATED');
INSERT INTO location_accuracy (id, name) VALUES (3, 'GEOMETRIC_CENTER');
INSERT INTO location_accuracy (id, name) VALUES (2, 'APPROXIMATE');
INSERT INTO location_accuracy (id, name) VALUES (1, 'INVALID');
