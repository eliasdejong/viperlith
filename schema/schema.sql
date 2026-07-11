PRAGMA page_size = 4096;
PRAGMA journal_mode = WAL;


create table if not exists messages (
	id integer primary key,
	conversation_id integer not null references conversations(id) on delete cascade,
	sequence_nr integer not null,
	role text not null,
	content text not null,
	created_ts datetime default current_timestamp
);
create index idx_messages_conversation_id on messages(conversation_id);



create table if not exists conversations (
	id integer primary key,
	title text not null,
	user_id integer not null references users(id) on delete cascade
);
create index idx_conversations_user_id on conversations(user_id);



create table if not exists users (
	id integer primary key,
	session_id text not null,
	active_conversation_id integer references conversations(id) on delete set null
);
create index idx_users_session_id on users(session_id);