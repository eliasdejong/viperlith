create table if not exists channels (
	id integer primary key,
	name text unique not null,
	created_ts real not null default (unixepoch('now'))
);


create table if not exists users (
	id integer primary key,
	nickname text not null default ('user_' || hex(randomblob(4))),	
	session_id text not null unique,
	current_channel_id integer references channels(id) on delete set null,
	created_ts real not null default (unixepoch('now'))
);
create index idx_users_session_id on users(session_id);


create table if not exists channel_memberships (
	user_id integer not null references users(id) on delete cascade,
	channel_id integer not null references channels(id) on delete cascade,
	role text not null check (role in ('admin', 'mod', 'member', 'guest', 'banned')),
	created_ts real not null default (unixepoch('now')),
	primary key (user_id, channel_id)
);
create index idx_channel_memberships_channel_id on channel_memberships(channel_id);


create table if not exists messages (
	id integer primary key,
	channel_id integer not null references channels(id) on delete cascade,
	user_id integer not null references users(id) on delete cascade,
	content text not null,
	created_ts real not null default (unixepoch('now'))
);
create index idx_messages_channel_ts on messages(channel_id, created_ts);
