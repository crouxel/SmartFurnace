CREATE TABLE [dbo].[A2]
(
  [Id] INT NOT NULL PRIMARY KEY,
  [Cycle] INT NOT NULL,
  [StartTemp] INT NOT NULL,
  [EndTemp] INT NOT NULL,
  [CycleType] NVARCHAR(50) NOT NULL,
  [CycleTime] NVARCHAR(50) NOT NULL
)

INSERT INTO [dbo].[A2] ([Id], [Cycle], [StartTemp], [EndTemp], [CycleType], [CycleTime])
VALUES (1, 1, 22, 649, 'ramp', '40 minutes'),
       (2, 2, 649, 649, 'soak', '60 minutes');