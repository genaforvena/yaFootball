drop table if exists players;
create table players (
  id integer primary key,
  telegram_handler text,
  name text,
  ya_handler text);

drop table if exists matches;
create table matches (
  id integer primary key autoincrement,
  players_limit integer not null,
  place text not null,
  time integer);

drop table if exists players_in_match;
create table players_in_match (
  match_id integer not null,
  player_id integer not null);
