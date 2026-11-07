# शिवराम Studio

A single-page Nepali text-to-video editor. Write a script, generate slides, add AI pictures, music and branding, then export a vertical MP4.

## Run locally

```bash
npm start
```

Open <http://localhost:8765> (the included `.env` sets `PORT=8765`; without a `.env` the server uses port 10000, or the `PORT` your host provides).

No npm packages are required — the server uses Node's built-in `http` and `fetch`.

## Slide pictures (Cloudflare + Pollinations fallback)

Every slide gets a picture automatically when you press **Make slides**.

- If the slide contains an `@img: description` line, that description is used as the image prompt.
- Otherwise the server summarizes the slide text in English, then generates the picture.
- Cloudflare Workers AI (`@cf/black-forest-labs/flux-1-schnell`) is tried first.
- If Cloudflare is out of its free daily neurons, rate-limited, or returns an error, the server automatically switches to Pollinations (`gen.pollinations.ai`) for the prompt summary and the picture.
- The switch happens per slide. If Cloudflare made 4 pictures and then hit its limit, the remaining slides continue with Pollinations instead of stopping or starting over.
- The browser only talks to `/api/slide-image`; both API keys stay on the server.

### Safety

Pictures are constrained for religious and cultural use:

- The summary prompt requires respectful, family-friendly scenes, fully clothed people in modest attire, and no violence or disturbing imagery.
- Explicit `@img` prompts are screened. If one contains unsafe wording, the server ignores it and summarizes the slide instead.
- Every final image prompt adds positive safety wording (modest clothing, respectful, serene).
- Both providers receive the same safe prompt. Pollinations additionally gets `safe=true` and a negative prompt that blocks nudity, violence, weapons, drugs, alcohol and text/watermarks.

This is a prompt-level safeguard, not a guarantee from the image model. Review generated pictures before publishing.

If Cloudflare is out of quota, the rest of the batch uses Pollinations automatically. If both providers fail, the app shows the reason from each one. Pollinations uses your Pollen balance, so it has its own limits.

### Credentials

Copy `.env.example` to `.env` and fill in:

```env
CLOUDFLARE_ACCOUNT_ID=...
CLOUDFLARE_API_TOKEN=...
POLLINATIONS_API=...
```

`POLLINATIONS_API` is optional but recommended. Without it there is no fallback when Cloudflare runs out. On a host such as Render, add all three variables in the service's environment settings. `.env` is ignored by Git and is never committed.

Optional overrides: `CLOUDFLARE_TEXT_MODEL`, `CLOUDFLARE_IMAGE_MODEL`, `CLOUDFLARE_IMAGE_STEPS`, `POLLINATIONS_IMAGE_MODEL`, `POLLINATIONS_TEXT_MODEL`, `PORT`.

## Files

- `index.html` — the whole editor (UI, timeline, canvas and export).
- `server.js` — static server, `/ping` health check, and the Cloudflare/Pollinations AI proxy.
- `editor.original.html` — untouched backup of the original editor.
