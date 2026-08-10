# Viperlith Architecture
## Introduction
Traditional SPA architectures expose JSON endpoints on the server, then build page elements on the frontend with JavaScript & reactive components. Hypermedia Driven Applications (HDA) instead render HTML markup on the server and then send it to the client to update (parts of) the screen.

Streaming hypermedia makes it possible to build rich interactive user experiences just using HTML, without requiring (heavy) JavaScript SPA frameworks like React, resulting in application that perform better and are generally simpler to build and maintain.

The [Tao of Datastar](https://data-star.dev/guide/the_tao_of_datastar) is a great starting point.


## Terminology
- **HTML**: HyperText Markup Language
- **HDA**: Hypermedia-Driven Applications
- **REST**: REpresentational State Transfer
- **SPA**: Single-Page Application
- **MPA**: Multi-Page Application
- **DOM**: Document Object Model (representation used internally by the browser to represent web pages)
- **morph**: merging a fragment of HTML into the DOM
- **SSE**: Server-Sent Events
- **SSR**: Server-Side Rendering
- **templating engine**: Tool for dynamically building string output, used to 'render' HTML responses
- **CQRS**: Command Query Responsibility Segregation
- **ACID**: Atomicity, Consistency, Isolation & Durability


## Brief history of the web
- **1991-2000 The Early Web**: Static HTML, cgi-bin, Perl scripts, FastCGI
- **2000-2006 The Dynamic Web**: PHP, ASP, JSP, LAMP-stack, CMSs (Wordpress, Drupal), Flash
- **2006-2010 The Ajax Era**: jQuery, Backbone.js, AJAX
- **2010-2015 The Frameworks Arrive**:  AngularJS, Ember, React, Vue, Ruby on Rails, Node.js
- **2012-2018 The Build Step Era**: webpack, NPM, Babel, Grunt/Gulp, JSX, TypeScript, CI/CD replaces FTP
- **2018-2024 The Tooling Arms Race**: Vite, esbuild, SWC, Bun, Turbopack, TailwindCSS, Next.js, Astro
- **2024-today The Pendulum Swings Back**: htmx, Alpine.js, Datastar, Rails Turbo/Hotwire, Server-rendered components

Notice the circle:
server-rendered HTML → thick clients → back to server-rendered HTML


## Core philosophy
The core of any interactive application can be expressed in a single formula:
```
	view = f(state)
```
The 'state' refers to the application state. The 'view' refers to the representation of that state, communicated to the outside world for humans.

For hypermedia-driven applications:
- **The state**: should be persisted on disk and therefore is stored in a database such as SQLite, Postgres or MySQL.
- **The view**: is an HTML string, exposed over a network API which is rendered by the client's browser.
- `f()`: is a rendering function which takes in the server state (DB) and outputs an HTML string. On the backend, this is done by combining SQL queries with a templating engine such as Jinja in Python or Templ in Go.


## Just use HTML
<img src="images/just_use_html_meme.jpg" alt="Just use HTML bell curve meme" width="675">

### Client-side state management
One of the more complex ongoing problems in the SPA world is client-side state management. Many solutions exists (Redux, Zustand, React Router).
Hypermedia-driven applications deal with this problem cleverly: **by eliminating client-side state** (and moving it to the backend).

Of course, not all client-side state can be eliminated. Some of it is necessary, such as user inputs, scroll position etc. Also, some state is considered *trivial*, meaning it does not affect anything meaningful. For example, whether dark mode is enabled or whether a dropdown menu is opened are mostly client-side visual artifacts that do not concern the server.

The result of eliminating client-side state is that the browser becomes a "dumb" viewport or terminal, capable only of displaying HTML.

### Obsoleting of the Virtual DOM
In the SPA world, the "virtual DOM" or "vdom" *Raison d'être* was to support fast dynamic page updates such as real-time updating of table data, because browsers at the time struggled with this, especially on low-end client hardware.

However, a lot has changed since 2013 and browsers have become a lot more capable. Meanwhile, internet speeds have improved dramatically while hardware has become more powerful. We can now rely on the **real DOM** to represent and update the page directly, without recreating the world in JavaScript.

Consider that many of the most performance-sensitive routines (parsing HTML, layout engine, font sizing, etc.) are highly optimized over decades of engineering, and are written in native languages such as C++, compiled for the target hardware. Meanwhile, JavaScript is a scripting language which runs in a background JIT compiler that demands high memory and startup times. The single-threaded model of JavaScript where the rendering blocks the main thread and vice-versa has also aged especially poorly into the multi-core era. Meanwhile, the browser is able leverage multithreading to parallelize much of this work.

### The Full Picture
```
                                                                  
                    Datastar Server Endpoints                     
                                                                  
   ┌──────────────────────────────────────────────────────┐       
   │                                                      │       
   │                 Web Server + database                │       
   │                                                      │       
   └──────────────┬───────────────────────────────────────┘       
             ▲    │                 ▲               ▲             
             │    │                 │               │             
             │    │                 │               │             
    GET      │    │ HTTP SSE        │POST           │POST         
    /updates │    │ response        │/button-click  │/form-submit 
             │    │ (kept open)     │               │             
             │    │                 │               │             
             │    ▼                 │               │             
   ┌─────────┴──────────────────────┴───────────────┴─────┐       
   │                                                      │       
   │                     Client browser                   │       
   │                                                      │       
   └──────────────────────────────────────────────────────┘       
                                                                  
```
Having the ability to render any HTML through templates, what do we need state on the client for? We can keep all state in the backend and simply send down the declarative HTML for what the client is supposed to see at any given moment over SSE. This drastically simplifies the picture on the client:

<img src="images/react_state_mgmt.webp" alt="React state management" width="800">

Relying on the browser for most functionality is not only viable, but in fact faster and more reliable than trying to recreate everything in JavaScript.

### The Magic Sauce: Idiomorph
[Idiomorph](https://github.com/bigskysoftware/idiomorph) is a sophisticated DOM-morphing algorithm, and Datastar uses its own adapted implementation.

This algorithm takes any fragment of HTML and *morphs* it into the local DOM, replacing or inserting content on the page. It is possible to target individual elements, or morph the entire page at once.

Practically, this means we no longer have to care about partial rendering or diffing for performance reasons. The server can send the **entire page** at once (known as a "fat morph"), and the algorithm on the client will only touch the real DOM where it needs to change. This allows us to render the whole page from a single function (`html = render(DB)`) on the backend, and simply re-render when the state (DB) changes. No manual diffing or VDOM required.

### Practically Cheating: Brotli Compression
One of the reputes against sending full-page replacements over the network is: "But what about bandwidth?".

Brotli is a compression algorithm similar to GZip or ZStandard, which is available by default in most browsers. It supports **streaming compression**, meaning we can compress HTTP responses "continuously" as they arrive. Crucially, the **compression context persists as long as a given response**. Meaning any data we send in a response can refer back and de-duplicate anything that came before it. Notice how well this synergizes with Datastar's encouraged use of Server-Sent Events and long-lived responses. Under the hood, this uses HTTP/1.1's [Chunked Transfer Coding](https://en.wikipedia.org/wiki/Chunked_transfer_encoding) or more efficient mechanisms for data streaming in HTTP/2.

An HTTP SSE response is kept open and we keep streaming HTML over it to the client. In practice, even when continuously re-sending the entire HTML page, no extra bytes are transmitted over the wire unless something changes. Over time, the bandwidth converges on only the *delta* of the page content. Idiomorph ensures we only touch the DOM where necessary when the content arrives.

### Relying on HTML for UI components
Relying on HTML extends not only to DOM updates, but also to UI components. HTML5 has acquired many native features such as datetime pickers, dialogs and more. We can simply use this instead of building our own. Some examples of UI component libraries that do this are [BasecoatUI](https://basecoatui.com/), [KelpUI](https://kelpui.com/) and [DaisyUI](https://daisyui.com/).


## Obsolete concepts
Because hypermedia-driven applications (HDA) are just sending HTML, a number of concepts common in the frontend industry become obsolete. Meaning they **cease to exist** as something a developer needs to think about:

### Build concepts
- babel translation
- tree shaking
- bundling
- code splitting

### React concepts
- client-side routing
- suspense
- useEffect
- useAsyncExternalStore
- dependency arrays
- prop drilling
- React compiler
- Immer
- vdom
- React context

### Rendering concepts
- (selective/partial/progressive) hydration
- use client/server
- (incremental/deferred) static regeneration


## Datastar vs HTMX
Whereas [htmx](https://htmx.org/) primarily relies on request-response (pull) interactions with partial HTML-fragments "patched" into the DOM, Datastar encourages a "push" model with full-page rebuilds similar to [immediate mode rendering](https://en.wikipedia.org/wiki/Immediate_mode_(computer_graphics)). These full page updates (known as "fat morphs") are sent directly to the client, replacing the entire contents of the screen at once.

The Datastar approach has the following advantages:
- When inserting partial HTML fragments with htmx, parts of the page can show stale data when sections are updated on different intervals. Datastar's full-page rebuilding eliminates most of these problems. Typically, the entire page can be constructed from a single `render()` function on the backend.
- Under the hood, Datastar uses a [sophisticated DOM-morphing algorithm](https://github.com/bigskysoftware/idiomorph) to make updates fast and appear seamless.
- Sending full page updates may raise concerns about network bandwidth. However, use of persistent SSE streams enables **streaming compression** across an entire session compared to mere individual requests. Using the browser's built-in [Brotli compression](https://en.wikipedia.org/wiki/Brotli), extra bytes are sent over the wire only if the content is changed. This achieves total compression ratio's upwards of 50-4000x, exceeding what is commonly attainable from gzipped responses.
- For some interactions, like showing a dropdown menu, sending a network request is undesirable. However HTMX provides very little in the way of client-side variables or interactivity, necessitating additional JavaScript frameworks such as [Alpine.js](https://alpinejs.dev/). While lightweight, these frameworks introduce additional APIs and overhead while [not always playing well with htmx](https://youtu.be/SjUoc8R1dzQ?si=mGA4nkLOCs49cAje&t=1431). Datastar instead has *signals* and a [lightweight set of attributes](https://data-star.dev/reference/attributes) to build client-side expressions, meaning another library isn't needed for the majority of use cases.

Datastar does not enfore any particular model, meaning it is possible to build applications like htmx or even SPAs. However, doing so is generally not recommended.


## Why Server-Sent Events?
First of all:
### What are Server-Sent Events?
To understand SSE, it is recommend to first watch [this overview video](https://www.youtube.com/watch?v=xq1dVQ-isb4).

For the full version, see [the WHATWG spec](https://html.spec.whatwg.org/#server-sent-events).

Short answer: SSE is an HTTP response type: `text/event-stream`. Other HTTP response types include `text/html`, `application/json` and `multipart/form-data`. Those are for HTML, JSON and form data respectively.

So what does the body of an SSE response look like?

Answer:
```
event: datastar-patch-elements
data: selector body
data: mode outer
data: elements <div>
data: elements		<button>Click me</button>
data: elements </div>


```
It is mostly just text. But notice the particular format with `event:`, `data:` and the two trailing endlines `\n\n`? That is part of the SSE response format.

### What SSE is NOT
SSE is NOT connection type, as it is **just HTTP** ([watch the video](https://www.youtube.com/watch?v=xq1dVQ-isb4)).

Another misconception: SSE is *always persistent*.

An SSE response can use HTTP/1.1 [Chunked Transfer Coding](https://en.wikipedia.org/wiki/Chunked_transfer_encoding) or data streaming mechanisms in HTTP/2 to keep sending data **as long as the server wants**. This means it can send one chunk, or multiple. The server is in control of when the response ends.

### So Why use SSE?
Because it places **the server** in control of when to send data (push vs pull). Additionally, it synergized well with native browser functionality, such as Brotli compression.


## Why not web sockets?
Because it does not synergize well with native browser functionality. Applications must handle stateful connections, reconnecting, and compression on the main thread in JavaScript. For HTTP, all of those are handled natively by the browser (in C++ background threads).

HTTP traffic also has the benefit of appearing more "normal" and thus has a lower chance of getting intercepted by some corporate firewalls.

In practice, **web sockets are a dead-end**.


## Web Server Architecture
### Simple Web Server + Database
A simple web server + database might look like this:
```
                                           
        Simple Web Server + Database       
                                           
              ┌─────────────┐              
              │  Web Server │              
              │             │              
              └──────┬──────┘              
                     │                     
                     │Read/Write           
                     │                     
   ┌─────────────────┴─────────────────┐   
   │                                   │   
   │         Postgres or MySQL         │   
   │                                   │   
   └───────────────────────────────────┘   
                                           
```
All is well, but if we have many users, traffic increases and our web server running on a single thread could get overloaded, especially if it is written in a scripting language such as Python or JavaScript.

### Web Workers + Database Architecture
To solve this, many web servers provide an option to run multiple workers, which will spawn either threads or processes to run in parallel:
```
                                                           
          Web Workers + Database Architecture              
                                                           
   ┌───────────────────────────────────────────────────┐   
   │                uvicorn --workers N                │   
   │                                                   │   
   │ ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   
   │ │  Web Worker │  │  Web Worker │  │  Web Worker │ │   
   │ │      1      │  │      2      │  │      N      │ │   
   │ └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │   
   └────────│────────────────│────────────────│────────┘   
            │                │                │            
            │Read/Write      │Read/Write      │Read/Write  
            │                │                │            
   ┌────────┴────────────────┴────────────────┴────────┐   
   │                                                   │   
   │                 Postgres or MySQL                 │   
   │                                                   │   
   └───────────────────────────────────────────────────┘   
                                                           
```
Each worker is stateless and receives a separate read/write connection to the database.

Great! We scaled web workers across the machine's core count.

However, we have now acquired a new bottleneck: **The database**.

Notice how each web worker has its own read/write connection to the database? Each worker is competing to schedule transactions. And because each transaction could be reading and writing to/from the same rows, the database has to coordinate this in an orderly fashion while maintaining **ACID**.

In particular:
- What happens if two workers try to edit the same row simultaneously?
- When do a worker's writes become visible to other workers?

The database has to ensure that each query sees a consistent, isolated view of the data, while making sure that changes are atomic.

From the user's perspective, it "just works" and the database seems to handle it fine. However, maintaining strong ACID guarantees does not come for free. Most databases hold **locks** when a particular piece of data is being modified. While the lock is held, **no other query can modify the same data protected by the lock**. This locking can lead to **contention** and performance problems under load.

Counter to popular belief, Postgres is **not ACID by default**. The default isolation level in Postgres 'read committed', which [allows for serialization anomalies, phantom reads and nonrepeatable reads](https://www.postgresql.org/docs/current/transaction-iso.html). To solve this problem, the isolation level must be set to 'serializable', however the documentation warns that:

> "applications using this level must be prepared to retry transactions due to serialization failures"

The story for MySQL is also not much better, with [the default isolation level of 'repeatable read'](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html) still allowing for serialization anomalies. Again, a 'serializable' level is available, however not without performance implications:

> InnoDB implicitly converts all plain SELECT statements to SELECT ... FOR SHARE

>  SELECT ... FOR SHARE
> Sets a shared mode lock on any rows that are read. Other sessions can read the rows, but cannot modify them until your transaction commits. If any of these rows were changed by another transaction that has not yet committed, your query waits until that transaction ends and then uses the latest values.

So while we can use multiple web workers, unless we are willing to compromise on ACID, we do not get the same scaling out of the database, as our concurrent transactions will be waiting to acquire locks.

What can we do about this?


### Switching to SQLite
First, we will switch our database to SQLite. An out-of-process databases such as Postgres has unnecessary overhead, such as:
- Running in a standalone process
- Localhost networking protocol + serialization
- Binary size
- Connection pooling
- Poor MVCC implementation[^1]
- File format portability
- If remote: TCP/IP + SSL/TLS
- Startup time

However, this will not actually solve the concurrency problem. If we simply copy the previous architecture, we will run into the infamous `SQLITE_BUSY` error.

So what to do?


### CQRS Architecture
In CQRS, database reads are separated from writes.

We will make a big change: web workers are themselves not allowed to write to the database. Instead, their connections are **read-only** and a separate 'single-writer' process holds **exclusive write access**. If a worker needs to affect a write to the database, it will place a command into the queue for the single-writer.

A "command" in this case means an "event to be processed by the single-writer". It could lead to a database write. Or not, depending on business logic. When a worker receives a request from a client, it will only validate the *shape* of the request. Workers themselves **DO NOT** process business logic. They simply enqueue commands for the single-writer to deal with.

This design effectively serializes all writes at the application layer, meaning `SQLITE_BUSY` is never encountered. Because workers read from the same `mmap` page cache, reads scale horizontally with core count without cache duplication. Writes are batched for maximum throughput while still being fully serialized & ACID. The single-writer will drain the queues and process commands on a fixed frame rate / interval. Batching makes it possible to reach as much as [a million inserts per second](https://andersmurphy.com/2026/06/05/the-perils-of-uuid-primary-keys-in-sqlite.html).

However, since each worker lives inside its own process, by default, they have no way of communicating with the writer's process. To solve this, we allocate the command queues in shared memory[^2].
```
                                                                                        
                               Viperlith CQRS Architecture                              
                                                                                        
   ┌───────────────────────┐    ┌───────────────────────────────────────────────────┐   
   │ Single-writer Process │    │                uvicorn --workers N                │   
   │ ┌─────────────────────┴────┴─────────────────────────────────────────────────┐ │   
   │ │                               MPSC command queue                           │ │   
   │ │                               (shared memory)                              │ │   
   │ └─────────┼───────────┬────┬───────────▲────────────────▲────────────────▲───┘ │   
   │  ┌────────▼─────────┐ │    │ ┌─────────┼───┐  ┌─────────┼───┐  ┌─────────┼───┐ │   
   │  │  Business Logic  │ │    │ │  Web Worker │  │  Web Worker │  │  Web Worker │ │   
   │  └────────┬─────────┘ │    │ │      1      │  │      2      │  │      N      │ │   
   │           │           │    │ └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │   
   └───────────│───────────┘    └────────│────────────────│────────────────│────────┘   
               │                         │                │                │            
               │Read/Write               │Read            │Read            │Read        
               │                         │                │                │            
   ┌───────────┴─────────────────────────┴────────────────┴────────────────┴────────┐   
   │                                                                                │   
   │                            SQLite (mmap + WAL mode)                            │   
   │                                                                                │   
   └────────────────────────────────────────────────────────────────────────────────┘   
                                                                                        
```
A typical interaction cycle goes like this:
1. User performs an action inside the UI
2. Fetch request is fired to an action endpoint (e.g. `/click-button`)
3. Web worker receives the request, validates its format and places a command in the MPSC queue
4. Single-writer takes the command from the queue
5. Single-writer applies business logic
6. Single-writer commits a write-transaction to the database
7. The write becomes visible to all workers
8. The worker holding the SSE stream to the client re-renders the page, based on the new database state
9. Client receives the new page and Datastar morphs it into their local DOM
10. Client sees the updated page

We now have obtained the following features:
1. Writes never block or run into locks
2. Readers and writers don't block eachother (ensured by WAL mode)
3. Readers scale horizontally with core count
4. No cache duplication / Readers read from the same page cache (ensured by mmap)
5. Batching unlocks further increased write throughput

Alas, we can increase worker count without running into concurrency problems!


[^1]: Postgres' MVCC implementation [has aged quite poorly](https://www.cs.cmu.edu/~pavlo/blog/2023/04/the-part-of-postgresql-we-hate-the-most.html). Long-running transactions can block the autovacuum process, which leaves behind more dead tuples, which in turn slow down transactions in a vicious cycle until the database halts to a crawl.
[^2]: Shared memory [is the fastest way of communicating between processes](https://chengxin.de/2021/ipc/).