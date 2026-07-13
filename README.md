# DatastarGPT


### Create directory for database file
	sudo mkdir -p /var/lib/datastar-gpt
	sudo chown $USER /var/lib/datastar-gpt



fuser -k 8000/tcp
lsof -i :8000