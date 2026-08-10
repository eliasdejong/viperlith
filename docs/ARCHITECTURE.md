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


## Core philosophy
The core of any interactive application can be expressed in a single formula:
```
	view = f(state)
```
The 'state' refers to the application state. The 'view' refers to the representation of that state, communicated to the outside world for humans.


## Client-side state management
One of the more complex unsolved problems in the SPA world is client-side state management. Many solutions exists (Redux, Zustand, React Router).
Hypermedia-driven applications deal with this problem cleverly: **by eliminating client-side state**.

Of course, not all client-side state can be eliminated. Some of it is necessarily local, such as user inputs, scroll position etc. Also, some state is considered **trivial**, meaning it does not affect anything meaningful. For example, whether dark mode is enabled or whether a dropdown menu is opened usually are purely client-side visual artifacts that do not concern the server.

The result of eliminating client-side state, is that the browser becomes a "dumb" viewport or terminal, capable only of rendering HTML.

![React state management](docs/images/react_state_mgmt.webp)


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
- For some interactions, like showing a dropdown menu, sending a network request is overkill. However HTMX provides very little in the way of client-side variables or interactivity, necessitating additional JavaScript frameworks such as [Alpine.js](https://alpinejs.dev/). While lightweight, these frameworks introduce additional APIs and overhead while [not always playing well with htmx](https://youtu.be/SjUoc8R1dzQ?si=mGA4nkLOCs49cAje&t=1431). Datastar instead has *signals* and a [lightweight set of attributes](https://data-star.dev/reference/attributes) to build client-side expressions, meaning you don't need another library for the majority of use cases.


## Why Server-Sent Events?
To understand SSE, it is recommend to first watch [this overview video](https://www.youtube.com/watch?v=xq1dVQ-isb4).




## Why not web sockets?



HTTP traffic also has the benefit of appearing more "normal" and thus has a lower chance of getting intercepted by some corporate firewalls.