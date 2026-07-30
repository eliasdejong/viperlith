# 🐍⚡🚀 Viperlith: the hypermedia based monolith for Python

This is a small and opinionated full stack [Datastar](https://data-star.dev/) framework.
Streaming hypermedia makes it possible to build rich interactive user experiences without requiring heavy SPA frontend frameworks, or writing even a single line of JavaScript, resulting in application that are faster and generally simpler to build and maintain.

It consists of the following components:
1. [Litestar ASGI framework](https://litestar.dev/): Uses up to [10x less memory as compared to FastAPI](https://github.com/kunesj/fastapi-litestar-memory-benchmark).
2. [MsgSpec](https://msgspec.dev/): A lot of FastAPI's memory is consumed by [Pydantic data validation](https://pydantic.dev/docs/validation/latest/get-started/). MsgSpec provides the same validation capabilities while being [an order of magnitude faster](https://msgspec.dev/benchmarks).
3. SQLite through [APSW](https://github.com/rogerbinns/apsw): SQLite offers minimal operation overhead, and when properly tuned, significantly outperforms Postgres & MySQL for most workloads. APSW provides more control, features and better debug information compared to Python's builtin `sqlite3` module.
4. [Jinja templates](https://jinja.palletsprojects.com/en/stable/): Templating engine used to render HTML templates.
5. [Tailwind CSS](https://tailwindcss.com/): For declarative styling directly inside the markup.
6. Brotli compression: Used in Litestar's `CompressionConfig` to minimize bandwidth for streaming HTML over the wire.


## Architecture
Traditional SPA architectures expose JSON/REST endpoints on the server, then build page elements on the frontend with JavaScript & reactive components. Hypermedia Driven Applications (HDA) instead render HTML markup on the server and then send it to the client to immediately update their view.

`datastar.js` is a 11kB script enabling HTML updates sent from the server to be 'morphed' into the local DOM over an SSE stream. The server dictates when updates are sent. Typically, the entire page can be constructed from a single `render()` function on the backend. For reference on SSE, see this [Server Sent Events overview video](https://www.youtube.com/watch?v=xq1dVQ-isb4).


## How to run
### 1: Create directory for database file in `/var/lib`
	sudo mkdir -p /var/lib/viperlith
	sudo chown $USER /var/lib/viperlith

### 2: Run the launch script
	./launch.sh


## Credits
Inspired by Anders Murphy's [Hyperlith](https://github.com/andersmurphy/hyperlith).