create table planets(name text, moons integer);
insert into planets values ('Earth', 1), ('Mars', 2), ('Jupiter', 95);
select 'sqlite: ' || count(*) || ' planets, ' || sum(moons) || ' moons' from planets;
select 'sqlite: most moons ' || name from planets order by moons desc limit 1;
select 'sqlite: version ' || substr(sqlite_version(), 1, 1);
