-- Seed difficulty levels data

INSERT INTO difficulty_levels (id, display_name, threshold_multiplier, max_distance_km, display_order, description) VALUES
    ('easy', 'Easy', 2.0, 10000, 1, 'Famous landmarks and major world cities'),
    ('medium', 'Medium', 1.4, 5000, 2, 'Well-known cities and notable locations'),
    ('hard', 'Hard', 1.0, 2500, 3, 'Lesser-known capitals and regional cities'),
    ('expert', 'Expert', 0.65, 1000, 4, 'Obscure locations and small nations')
ON CONFLICT (id) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    threshold_multiplier = EXCLUDED.threshold_multiplier,
    max_distance_km = EXCLUDED.max_distance_km,
    display_order = EXCLUDED.display_order,
    description = EXCLUDED.description;
