# 🐍⚡🚀 Viperlith: the hypermedia based monolith for Python



## Introduction
This is a small and opinionated full stack [Datastar](https://data-star.dev/) web application monolith, written in Python. A Discord-like chat sample application is currently implemented which allows real-time chat rooms, creating/removing channels and setting nicknames.

`datastar.js` is a lightweight (11kB) hypermedia framework [similar to HTMX](docs/HTML_STREAMING.md).

Hypermedia-driven applications (HDA), unlike SPA frameworks (e.g. React, Vue, Angular), **eliminate state and logic on the client side**. Instead, interactive logic is moved to the backend and page updates are streamed to the client as server-rendered templates over a Server-Sent Events stream and *morphed* into the local DOM.
This is a bit like streaming a movie, except the movie is HTML and you receive new content from updates and UI interactions. The client's browser is effectively reduced to a rendering viewport only capable of displaying raw HTML.



## Architecture
See [docs/HTML_STREAMING.md](docs/HTML_STREAMING.md) for an introduction to the concept of HTML streaming.

Also see: [the Tao of Datastar](https://data-star.dev/guide/the_tao_of_datastar)
and [Datastar: Why another framework?](https://data-star.dev/essays/why_another_framework).



## The Stack
Viperlith consists of the following components:
1. [Litestar ASGI framework](https://litestar.dev/): Uses up to [10x less memory as compared to FastAPI](https://github.com/kunesj/fastapi-litestar-memory-benchmark).
2. [uvicorn](https://uvicorn.dev/): Popular ASGI web server
3. [MsgSpec](https://msgspec.dev/): [Pydantic data validation](https://pydantic.dev/docs/validation/latest/get-started/) consumes a lot of memory. MsgSpec provides the same validation capabilities while [serializing an order of magnitude faster](https://msgspec.dev/benchmarks).
4. SQLite through [APSW](https://github.com/rogerbinns/apsw): Local SQLite offers minimal operational overhead, and when properly tuned, significantly outperforms Postgres & MySQL for most workloads. APSW provides better control, features and error handling compared to Python's builtin `sqlite3` module.
5. [Jinja templates](https://jinja.palletsprojects.com/en/stable/): Templating engine used to render HTML templates.
6. [Tailwind CSS](https://tailwindcss.com/): For declarative styling directly inside the markup.
7. Brotli compression: Used in Litestar's `CompressionConfig` to minimize bandwidth for streaming HTML over the wire.



## How to run
### 1. Create `.env` file
Copy `.env.example` and rename it to `.env`. Change configurations if necessary.

### 2: Create directory for database file in `/var/lib`
	sudo mkdir -p /var/lib/viperlith
	sudo chown $USER /var/lib/viperlith

### 3: (Optional) Enable launch script permissions
	sudo chmod +x ./launch.sh

### 4: Run the launch script
	./launch.sh



## Credits
Inspired by Anders Murphy's [Hyperlith](https://github.com/andersmurphy/hyperlith).