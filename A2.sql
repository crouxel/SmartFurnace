DROP TABLE IF EXISTS A2;
CREATE TABLE IF NOT EXISTS A2 (
  Id INTEGER PRIMARY KEY,
  Cycle INTEGER NOT NULL,
  StartTemp INTEGER NOT NULL,
  EndTemp INTEGER NOT NULL,
  CycleType TEXT NOT NULL,
  CycleTime TIME NOT NULL,  -- Ensure this is INTEGER
  Notes TEXT NOT NULL
);

INSERT INTO A2 (Id, Cycle, StartTemp, EndTemp, CycleType, CycleTime, Notes)
VALUES (1, 1, 22, 649, 'Ramp', '00:40:00', 'Stress Relieve'),  -- Use TIME value
       (2, 2, 649, 649, 'Soak', '01:30:00', 'Stress Relieve'),
       (3, 3, 649, 760, 'Ramp', '00:10:00', 'PreHeat'),
       (4, 4, 760, 760, 'Soak', '00:30:00', 'PreHeat'),
       (5, 5, 760, 982, 'Ramp', '00:15:00', 'Austenizing'),
       (6, 6, 982, 982, 'Soak', '01:00:00', 'Austinizing'),
       (7, 7, 982, 22, 'Ramp', '01:30:00', 'Air Cool');