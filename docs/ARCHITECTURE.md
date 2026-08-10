# Viperlith Architecture
## Introduction
Traditional SPA architectures expose JSON endpoints on the server, then build page elements on the frontend with JavaScript & reactive components. Hypermedia Driven Applications (HDA) instead render HTML markup on the server and then send it to the client to update (parts of) the screen.

Streaming hypermedia makes it possible to build rich interactive user experiences just using HTML, without requiring (heavy) JavaScript SPA frameworks like React, resulting in application that perform better and are generally simpler to build and maintain.

The [Tao of Datastar](https://data-star.dev/guide/the_tao_of_datastar) is a great starting point.


## Terminology
- HTML: HyperText Markup Language
- HDA: Hypermedia-Driven Applications
- REST: REpresentational State Transfer
- SPA: Single-Page Application
- MPA: Multi-Page Application
- DOM: Document Object Model (representation used internally by the browser to represent web pages)
- morph: efficiently merging a fragment of HTML into the DOM
- SSE: Server-Sent Events
- SSR: Server-Side Rendering
- templating engine: Tool for dynamically building string output, used to 'render' HTML responses.


## Brief history of the web
- **1991-2000 The Early Web**: Static HTML, `cgi-bin`, Perl scripts, FastCGI
- **2000-2006 The Dynamic Web**: PHP, ASP, JSP, LAMP-stack, CMSs (Wordpress, Drupal), Flash
- **2006-2010 The Ajax Era**: jQuery, Backbone.js, AJAX
- **2010-2015 The Frameworks Arrive**:  AngularJS, Ember, React, Vue, Ruby on Rails, Node.js
- **2012-2018 The Build Step Era**: webpack, NPM, Babel, Grunt/Gulp, JSX, TypeScript, CI/CD replaces FTP
- **2018-2024 The Tooling Arms Race**: Vite, esbuild, SWC, Bun, Turbopack, TailwindCSS, Next.js, Astro
- **2024-today The Pendulum Swings Back**: htmx, Alpine.js, Datastar, Rails Turbo/Hotwire, Server-rendered components

Notice the circle:
`server-rendered HTML → thick clients → back to server-rendered HTML`


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


## Client-side state management
One of the more complex unsolved problems in the SPA world is client-side state management. Many solutions exists (Redux, Zustand, React Router).
Hypermedia-driven applications deal with this problem cleverly: **by eliminating client-side state** (and moving it to the backend).

Of course, not all client-side state can be eliminated. Some of it is necessary, such as user inputs, scroll position etc. Also, some state is considered *trivial*, meaning it does not affect anything meaningful. For example, whether dark mode is enabled or whether a dropdown menu is opened usually are purely client-side visual artifacts that do not concern the server.

The result of eliminating client-side state is that the browser becomes a "dumb" viewport or terminal, capable only of displaying HTML.

In the React world, the "virtual DOM" or "vdom"'s orginal purpose was to support fast dynamic page updates that the browser itself struggled with, such as real-time updating table data. However, a lot has changed since 2013 and browsers have become a lot more capable. 

<img src="images/react_state_mgmt.webp" alt="React state management" width="800">


## Obsolete concepts
Because hypermedia-driven applications (HDA) are just sending HTML, a number of concepts common in the frontend industry become obsolete. Meaning they cease to exist as something a developer needs to think about:
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
To understand SSE, it is recommend to first watch [this overview video](https://www.youtube.com/watch?v=xq1dVQ-isb4).




## Why not web sockets?



HTTP traffic also has the benefit of appearing more "normal" and thus has a lower chance of getting intercepted by some corporate firewalls.