-- Update country_challenges difficulty based on country area (smaller = harder).
-- Thresholds (km²):
--   expert : area <     10 000   (tiny island nations)
--   hard   : area <    100 000
--   medium : area <  1 000 000
--   easy   : area >= 1 000 000

UPDATE country_challenges cc
SET difficulty = CASE
    WHEN c.area_km2 <     10000 THEN 'expert'
    WHEN c.area_km2 <    100000 THEN 'hard'
    WHEN c.area_km2 <  1000000 THEN 'medium'
    ELSE                             'easy'
END
FROM countries c
WHERE LOWER( c.name ) = LOWER( cc.country );
