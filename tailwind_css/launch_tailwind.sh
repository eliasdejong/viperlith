#!/bin/bash

if ! [ -e tailwindcss ]
then
	echo Downloading Tailwind CSS binary...
	curl -sL https://github.com/tailwindlabs/tailwindcss/releases/download/v4.3.3/tailwindcss-linux-x64 -o tailwindcss
	chmod +x tailwindcss
fi

echo Starting Tailwind CSS...
./tailwindcss -i ../static/input.css -o ../static/output.css --watch --minify