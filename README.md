# शिवराम Studio

A single-page Nepali text-to-video editor. Write a script, generate slides, add AI pictures, music and branding, then export a vertical MP4.

## Run locally

```bash
npm start
```

Open <http://localhost:8765> (the included `.env` sets `PORT=8765`; without a `.env` the server uses port 10000, or the `PORT` your host provides).

No npm packages are required — the server uses Node's built-in `http` and `fetch`.

## Slide pictures (Cloudflare Workers AI)

Every slide gets a picture automatically when you press **Make slides**.

- If the slide contains an `@img: description` line, that description is used as the image prompt.
- Otherwise the server summarizes the slide text in English with a Workers AI text model, then generates the picture with `@cf/black-forest-labs/flux-1-schnell`.
- The browser only talks to `/api/slide-image`; the Cloudflare token stays on the server.

### Safety

Pictures are constrained for religious and cultural use:

- The summary prompt requires respectful, family-friendly scenes, fully clothed people in modest attire, and no violence or disturbing imagery.
- Explicit `@img` prompts are screened. If one contains unsafe wording, the server ignores it and summarizes the slide instead.
- Every final image prompt adds positive safety wording (modest clothing, respectful, serene).

This is a prompt-level safeguard, not a guarantee from the image model. Review generated pictures before publishing.

If the free daily Cloudflare AI allocation runs out, the app says so; wait for the reset or upgrade the Workers plan.

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
