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
In the SPA world, the "virtual DOM" or "vdom" *Raison d'être* was to support fast dynamic page updates such as real-time updating table data, because browsers at the time struggled with this, especially on low-end client hardware.

However, a lot has changed since 2013 and browsers have become a lot more capable. Meanwhile, internet speeds have improved dramatically while hardware has become more powerful. We can now rely on the **real DOM** to represent and update the page directly, without recreating the world in JavaScript.

Consider that many of the most performance-sensitive routines (parsing HTML, layout engine, font sizing, etc.) are highly optimized over decades of engineering, and are written in native languages such as C++, compiled for the target hardware. Meanwhile, JavaScript is a scripting language which runs in a background JIT compiler that demands high memory and startup times. The single-threaded model of JavaScript where the rendering blocks the main thread and vice-versa has also aged especially poorly into the multi-core era. Meanwhile, the browser is able leverage multithreading to parallelize much of this work.

### The Full Picture
Having the ability to render any HTML through templates, what do we need state on the client for? We can keep all state in the backend and simply send down the declarative HTML for what the client is supposed to see at any given moment. This drastically simplifies the picture on the client:

<img src="images/react_state_mgmt.webp" alt="React state management" width="800">

Relying on the browser for most functionality is not only viable, but in fact faster and more reliable than trying to recreate everything in JavaScript for the same result.

### The Magic Sauce: Idiomorph
[Idiomorph](https://github.com/bigskysoftware/idiomorph) is a sophisticated DOM-morphing algorithm, and Datastar uses its own adapted implementation.

This algorithm takes any fragment of HTML and *morphs* it into the local DOM, replacing or inserting content on the page. It is possible to target individual elements, or morph the entire page at once.

Practically, this means we no longer have to care about partial rendering or diffing for performance reasons. We can send the **entire page** at once (known as a "fat morph"), and the algorithm will only touch the real DOM where it needs to change. This allows us to render the whole page from a single function (`html = render(DB)`) on the backend, and simply re-render when the state (DB) changes. No manual diffing or VDOM required.

### Practically Cheating: Brotli Compression
One of the reputes against sending full-page replacements over the network is: "But what about bandwidth?".
Brotli is a compression algorithm similar to GZip or ZStandard, which is available by default in most browsers. It supports **streaming compression**, meaning we can compress HTTP responses "continuously" as they arrive. Crucially, the **compression context persists as long as a given response**. Meaning any data we send in a response can refer back and de-duplicate anything that came before it. Notice how well this synergizes with Datastar's encouraged use of Server Sent Events and long-lived responses. Under the hood, this uses HTTP/1.1's [Chunked Transfer Coding](https://en.wikipedia.org/wiki/Chunked_transfer_encoding) or more efficient mechanisms for data streaming in HTTP/2.

An HTTP SSE response is kept open and we keep streaming HTML over it to the client. Even continuously re-sending the entire HTML page, no extra bytes are transmitted over the wire unless something changes. Over time, the bandwidth converges on only the *delta* of the page content. Idiomorph ensures we only touch the DOM where necessary.

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