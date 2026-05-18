# React + Tailwind CSS + Vite

A minimal React application scaffold using Vite as the build tool and Tailwind CSS for styling.

## Prerequisites

- Node.js 18+
- npm 9+

## Setup

Install dependencies:

```bash
npm install
```

## Development

Start the dev server with hot module replacement:

```bash
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

## Build

Compile and minify for production:

```bash
npm run build
```

Output is written to the `dist/` directory.

## Preview

Preview the production build locally:

```bash
npm run preview
```

## Project Structure

```
├── index.html          # Vite entry point
├── vite.config.js      # Vite configuration
├── tailwind.config.js  # Tailwind CSS configuration
├── postcss.config.js   # PostCSS configuration
└── src/
    ├── main.jsx        # React entry point
    ├── index.css       # Global styles (Tailwind directives)
    ├── App.jsx         # Root application component
    └── components/     # Feature components (Header, Sidebar, MainContent)
```
