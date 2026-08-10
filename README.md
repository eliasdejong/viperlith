# 🐍⚡🚀 Viperlith: the hypermedia based monolith for Python

This is a small and opinionated full stack [Datastar](https://data-star.dev/) web application monolith.

Streaming hypermedia makes it possible to build the same rich interactive user experiences just using HTML, without requiring (heavy) JavaScript SPA frameworks like React, resulting in application that perform better and are generally simpler to build and maintain.

It consists of the following components:
1. [Litestar ASGI framework](https://litestar.dev/): Uses up to [10x less memory as compared to FastAPI](https://github.com/kunesj/fastapi-litestar-memory-benchmark).
2. [MsgSpec](https://msgspec.dev/): [Pydantic data validation](https://pydantic.dev/docs/validation/latest/get-started/) consumes a lot of memory. MsgSpec provides the same validation capabilities while [serializing an order of magnitude faster](https://msgspec.dev/benchmarks).
3. SQLite through [APSW](https://github.com/rogerbinns/apsw): Local SQLite offers minimal operational overhead, and when properly tuned, significantly outperforms Postgres & MySQL for most workloads. APSW provides better control, features and error handling compared to Python's builtin `sqlite3` module.
4. [Jinja templates](https://jinja.palletsprojects.com/en/stable/): Templating engine used to render HTML templates.
5. [Tailwind CSS](https://tailwindcss.com/): For declarative styling directly inside the markup.
6. Brotli compression: Used in Litestar's `CompressionConfig` to minimize bandwidth for streaming HTML over the wire.


## Architecture
Traditional SPA architectures expose JSON/REST endpoints on the server, then build page elements on the frontend with JavaScript & reactive components. Hypermedia Driven Applications (HDA) instead render HTML markup on the server and then send it to the client to update (parts of) the screen.

`datastar.js` is a 11kB script / hypermedia framework enabling HTML updates sent from the server to be *morphed* into the local DOM over a Server-Sent Events stream. The server dictates when updates are sent. Typically, the entire page can be constructed from a single `render()` function on the backend. For reference on SSE, see [this overview video](https://www.youtube.com/watch?v=xq1dVQ-isb4).


## Compared to HTMX
Whereas [htmx](https://htmx.org/) primarily relies on request-response (pull) interactions with partial HTML-fragments "patched" into the DOM, Datastar encourages a "push" model with full-page rebuilds similar to [immediate mode rendering](https://en.wikipedia.org/wiki/Immediate_mode_(computer_graphics)). These full page updates (known as "fat morphs") are sent directly to the client, replacing the entire contents of the screen at once.

The Datastar approach has the following advantages:
- When inserting partial HTML fragments with htmx, parts of the page can show stale data when sections are updated on different intervals. Datastar's full-page rebuilding eliminates most of these problems.
- Under the hood, Datastar uses a [sophisticated DOM-morphing algorithm](https://github.com/bigskysoftware/idiomorph) to make updates fast and appear seamless.
- Sending full page updates may raise concerns about network bandwidth. However, use of persistent SSE streams enables **streaming compression** across an entire session compared to mere individual requests. Using the browser's built-in [Brotli compression](https://en.wikipedia.org/wiki/Brotli), extra bytes are sent over the wire only if the content is changed. This achieves total compression ratio's upwards of 50-4000x, exceeding what is commonly attainable from gzipped responses.
- For some interactions, like showing a dropdown menu, sending a network request is overkill. However HTMX provides very little in the way of client-side variables or interactivity, necessitating additional JavaScript frameworks such as [Alpine.js](https://alpinejs.dev/). While lightweight, these frameworks introduce additional APIs and overhead while [not always playing well with htmx](https://youtu.be/SjUoc8R1dzQ?si=mGA4nkLOCs49cAje&t=1431). Datastar instead ships with *signals* and a [lightweight set of attributes](https://data-star.dev/reference/attributes) to build client-side expressions, meaning you don't need another library for the majority of use cases.


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