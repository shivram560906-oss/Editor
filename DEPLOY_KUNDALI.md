# Kundali on Render — deployment guide

The editor (Node) and the Kundali engine (Python) run as two Render web
services. The editor keeps its existing URL; it forwards `/api/kundali/*` to
the engine through `KUNDALI_BACKEND_URL`.

```
Browser -> https://shivram.onrender.com (Node)
        -> https://shivram-kundali.onrender.com (Python/FastAPI)
```

## 1. Deploy the Python engine

Use the Blueprint (recommended):

1. Open <https://dashboard.render.com/>.
2. **New +** -> **Blueprint**.
3. Select the `shivram560906-oss/Editor` repo and apply.
4. Render creates **shivram-kundali** from `render.yaml` with:
   - Dockerfile: `Kundali-Desktop/backend/Dockerfile`
   - Health check: `/health/live`
   - Plan: Free
5. Wait for the deploy to finish. The service URL is shown at the top
   (usually `https://shivram-kundali.onrender.com`).

Manual alternative:

- **New +** -> **Web Service** -> same repo.
- Language: **Docker**
- Name: `shivram-kundali`
- Branch: `main`
- Dockerfile Path: `Kundali-Desktop/backend/Dockerfile`
- Health Check Path: `/health/live`
- Instance Type: **Free**

Check it directly:

```
https://shivram-kundali.onrender.com/health/live
```

Expected: `{"status":"online","version":"2.0.0"}`

## 2. Point the editor at the engine

1. Render Dashboard -> **shivram** (the existing Node service).
2. **Environment** -> **Add Environment Variable**.
3. Key: `KUNDALI_BACKEND_URL`
   Value: `https://shivram-kundali.onrender.com`
4. **Save Changes** (this redeploys the editor).

If the Blueprint gave the engine a different URL, use that URL instead.

## 3. Verify

```
https://shivram.onrender.com/places.json          -> 200 JSON
https://shivram.onrender.com/api/kundali/places   -> 200 JSON (65 countries)
```

Then open the site, choose **Kundali -> New**, pick Nepal -> Bagmati ->
Kathmandu (latitude/longitude/timezone fill automatically) and calculate.

## Notes

- Free services sleep after ~15 minutes idle. The first request after sleep
  can take up to a minute; the country list still loads instantly from
  `places.json`, and the calculation timeout is 3 minutes.
- `places.json` is generated from the engine. If the city dataset changes,
  regenerate it and bump `kunPlacesV1` in `index.html` so browsers refresh
  their cache.
- The engine stores data in SQLite inside the container. Free Render
  services have no persistent disk, so that data resets on redeploy. Kundali
  calculations do not depend on it.
