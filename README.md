# शिवराम Studio

A single-page Nepali text-to-video editor. Write a script, generate slides, add AI pictures, music and branding, then export a vertical MP4.

## Run locally

```bash
npm start
```

Open <http://localhost:8765>.

No npm packages are required — the server uses Node's built-in `http` and `fetch`.

## Slide pictures (Cloudflare Workers AI)

Every slide gets a picture automatically when you press **Make slides**.

- If the slide contains an `@img: description` line, that description is used as the image prompt.
- Otherwise the server summarizes the slide text in English with a Workers AI text model, then generates the picture with `@cf/black-forest-labs/flux-1-schnell`.
- The browser only talks to `/api/slide-image`; the Cloudflare token stays on the server.

### Credentials

Copy `.env.example` to `.env` and fill in:

```env
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_API_TOKEN=...
```

On a host such as Render, add the same two variables in the service's environment settings. `.env` is ignored by Git and is never committed.

Optional overrides: `CLOUDFLARE_TEXT_MODEL`, `CLOUDFLARE_IMAGE_MODEL`, `CLOUDFLARE_IMAGE_STEPS`, `PORT`.

## Files

- `index.html` — the whole editor (UI, timeline, canvas and export).
- `server.js` — static server, `/ping` health check, and the Cloudflare AI proxy.
- `editor.original.html` — untouched backup of the original editor.
