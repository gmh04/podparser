ALTER TABLE location ADD COLUMN position integer;
COMMENT ON COLUMN location.position IS 'the position of the location in relation to the original address';