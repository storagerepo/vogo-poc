# Vogo Dreams

A premium, cinematic and highly interactive travel experience built with **React + Vite + TypeScript + Tailwind CSS**.

## Tech Stack

- ⚛️ **React 19** — UI library
- ⚡ **Vite 8** — lightning-fast build tool and dev server
- 🔷 **TypeScript** — type safety
- 🎨 **Tailwind CSS v4** — utility-first styling
- 🎞️ **Framer Motion** — cinematic animations and transitions
- 🌐 **React Three Fiber / Three.js** — 3D globe and interactive elements

## Getting Started

Requires [Node.js](https://nodejs.org/) and npm.

```sh
git clone <this-repository-url>
cd <repository-name>
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start local dev server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run lint` | Run ESLint |
| `npm run format` | Format code with Prettier |

## Project Structure

```
src/
├── assets/          # Images and static assets
├── components/
│   ├── ui/          # Reusable UI primitives (shadcn/ui)
│   └── vogo/        # Page-specific components
│       ├── site-nav.tsx
│       ├── hero.tsx
│       ├── destinations.tsx
│       ├── trending-properties.tsx
│       ├── property-types.tsx
│       ├── traveler-destinations.tsx
│       ├── partner-strip.tsx
│       ├── final-cta.tsx
│       └── ...
├── hooks/           # Custom React hooks
├── lib/             # Utilities (cn, etc.)
├── App.tsx          # Root component
├── main.tsx         # React entry point
└── styles.css       # Global styles + Tailwind theme
```
