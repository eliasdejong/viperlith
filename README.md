# 🐍⚡🚀 Viperlith: the hypermedia based monolith for Python

This is a small and very opinionated fullstack [Datastar](https://data-star.dev/) framework.
Streaming hypermedia makes it possible to build rich interactive user experiences without requiring heavy SPA frontend frameworks, or writing even a single line of JavaScript. Resulting application are faster and generally much simpler to build and maintain.

It consists of the following components:
1. [Litestar ASGI framework](https://litestar.dev/): Uses up to [10x less memory as compared to FastAPI](https://github.com/kunesj/fastapi-litestar-memory-benchmark).
2. [MsgSpec](https://msgspec.dev/): A lot of FastAPI's memory is consumed by [Pydantic data validation](https://pydantic.dev/docs/validation/latest/get-started/). MsgSpec provides the same validation capabilities while being [an order of magnitude faster](https://msgspec.dev/benchmarks).
3. SQLite through [APSW](https://github.com/rogerbinns/apsw): SQLite offers minimal operation overhead, and when properly tuned, significantly outperforms Postgres & MySQL for most workloads. By serializing writes on the application layer, the infamous `SQLITE_BUSY` error can be entirely avoided.
4. `spsc_ring_threadsafe`: A thread-safe SPSC queue for Python, implemented on a ring buffer written in C. Used with shared memory to queue commands from workers to the single-writer.
5. [Jinja templates](https://jinja.palletsprojects.com/en/stable/): Templating engine used to render HTML templates.
6. [Tailwind CSS](https://tailwindcss.com/): For declarative styling directly inside the markup.
7. Brotli compression: Used in Litestar's `CompressionConfig` to minimize bandwidth for streaming HTML over the wire.

## Architecture
Traditional SPA architectures expose JSON/REST endpoints on the server, then build page elements on the frontend with JavaScript & reactive components. Hypermedia Driven Applications (HDA) instead render HTML markup on the server and then send it to the client to immediately update their view.

`datastar.js` is a 11kB script enabling HTML updates sent from the server to be 'morphed' into the local DOM over an SSE stream. The server dictates when updates are sent. Typically, the entire page can be constructed from a single `render()` function on the backend. For reference, see the [TAO of Datastar](https://data-star.dev/guide/the_tao_of_datastar/), [Hyperlth README](https://github.com/andersmurphy/hyperlith/blob/master/README.md) and [Server Sent Events Overview (video)](https://www.youtube.com/watch?v=xq1dVQ-isb4).

Viperlith uses a CQRS architecture where reads are separated from writes.
Web workers handling requests are themselves not allowed to write to the database. Instead, a standalone 'single-writer' process has exclusive write access:
```
                            Viperlith CQRS Architecture                           
                                                                                  
┌───────────────────────┐    ┌───────────────────────────────────────────────────┐
│ Single-writer process │    │                uvicorn --workers N                │
│                       │    │ ┌─────────────┐                                   │
│  ┌─────────────────┐  │    │ │  Web Worker │                                   │
│  │                 ├──│────│─┤      1      │  ┌─────────────┐                  │
│  │ MPSC queue      │  │    │ └──────┬──────┘  │  Web Worker │                  │
│  │ (shared memory) ├──│────│────────│─────────┤      2      │  ┌─────────────┐ │
│  │                 │  │    │        │         └──────┬──────┘  │  Web Worker │ │
│  │                 ├──│────│────────│────────────────│─────────┤      N      │ │
│  └─────────────────┘  │    │        │                │         └─────┬───────┘ │
└───────────┬───────────┘    └────────│────────────────│───────────────│─────────┘
            │                         │                │               │          
            │Read/Write               │Read            │Read           │Read      
            │                         │                │               │          
┌───────────┴─────────────────────────┴────────────────┴───────────────┴─────────┐
│                                                                                │
│                            SQLite (mmap + WAL mode)                            │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```
If a client request needs to affect a write to the database, the worker will place a command into the queue for the single-writer. The latter will drain the queues and process commands on a fixed interval. It also uses nested transactions (`SAVEPOINT`) to batch writes and get extra performance.

This design effectively serializes all writes at the application layer, meaning `SQLITE_BUSY` is never encountered in practice. Because workers can read from the same `mmap` cache, reads scale horizontally with core count. Writes are batched for maximum throughput while still being fully serialized & ACID.

A typical interaction cycle might go like this:
1. User performs an action inside the UI
2. Fetch request is fired to an action endpoint (e.g. `/click-button`)
3. Web worker receives the request, and places a command in the MPSC queue
4. Single-writer reads the command from the queue
5. Single-writer updates the server state by committing a write-transaction
6. The write becomes visible to all workers
7. The worker holding the SSE stream to the client re-renders the page, based on the new server state
8. The worker holding the SSE stream sends the new page over the stream (brotli compressed)
9. Client receives the new page and Datastar morphs it into their local DOM
10. Client sees the updated page


## Create directory for database file in `/var/lib`
	sudo mkdir -p /var/lib/viperlith
	sudo chown $USER /var/lib/viperlith

## Remove OpenAI
This project includes [openai](https://github.com/openai/openai-python) for the LLM demo. If you don't need it, remove it like so:
	uv remove openai

## Credits
Inspired by Anders Murphy's [Hyperlith](https://github.com/andersmurphy/hyperlith).