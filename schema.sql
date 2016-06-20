drop table if exists epitets;
create table epitets (
	id integer not null primary key autoincrement,
	epitet text not null unique,
	used boolean not null
);

drop table if exists names;
create table names (
	id integer primary key autoincrement,
	name text not null unique,
	epitet_id integer null references epitets
);