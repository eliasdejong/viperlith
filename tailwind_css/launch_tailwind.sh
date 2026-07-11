#!/bin/bash

if ! [ -e tailwindcss ]
then
	echo Downloading Tailwind CSS binary...
	curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/download/v4.3.1/tailwindcss-linux-x64
	chmod +x tailwindcss-linux-x64
	mv tailwindcss-linux-x64 tailwindcss
fi

echo Starting Tailwind CSS...
./tailwindcss -i ../static/input.css -o ../static/output.css --watch --minify