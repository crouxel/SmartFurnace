-- filepath: /c:/Users/crouxel/AppData/Documents/PROJECTS/SmartFurnace/A2.sql
DROP TABLE IF EXISTS A2;
CREATE TABLE IF NOT EXISTS A2 (
  Id INTEGER PRIMARY KEY,
  Cycle INTEGER NOT NULL,
  StartTemp INTEGER NOT NULL,
  EndTemp INTEGER NOT NULL,
  CycleType TEXT NOT NULL,
  CycleTime TEXT NOT NULL,
  Notes TEXT NOT NULL
);

INSERT INTO A2 (Id, Cycle, StartTemp, EndTemp, CycleType, CycleTime, Notes)
VALUES (1, 1, 22, 649, 'Ramp', '1 minutes','Stress Relieve'),
       (2, 2, 649, 649, 'Soak', '2 minutes','Stress Relieve'),
       (3, 3, 649, 760, 'Ramp', '2 minutes','PreHeat'),
       (4, 4, 760, 760, 'Soak', '2 minutes','PreHeat'),
       (5, 5, 760, 982, 'Ramp', '2 minutes','Austenizing'),
       (6, 6, 982, 982, 'Soak', '2 minutes', 'Austinizing'),
       (7, 7, 982, 22, 'Ramp', '2 minutes','Air Cool');