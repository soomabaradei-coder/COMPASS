# Deploying COMPASS (cloud pilot — Render)

This turns COMPASS into a public web portal + installable app that anyone can use.
Everything here is free. You need two free accounts: **GitHub** and **Render**.

---

## Step 1 — Put the code on GitHub

1. Create a free account at https://github.com and click **New repository** → name it `compass` → **Create**.
2. On the new repo page, follow "…or push an existing repository from the command line".
   From the `~/compass-app` folder run (the repo is already committed locally):
   ```
   git remote add origin https://github.com/<your-username>/compass.git
   git branch -M main
   git push -u origin main
   ```
   (GitHub will ask you to sign in / paste a token the first time.)

## Step 2 — Deploy on Render

1. Create a free account at https://render.com and click **New +** → **Web Service**.
2. Connect your GitHub and pick the `compass` repository.
3. Render auto-detects the settings from `render.yaml`. If it asks, use:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn wsgi:app --bind 0.0.0.0:$PORT`
   - **Instance type:** Free
4. Click **Create Web Service**. First build takes a few minutes.
5. You get a public URL like `https://compass-xxxx.onrender.com` — that's the **web portal**,
   already served over HTTPS.

## Step 3 — Install it as an app (on a phone)

Open the URL in the phone browser:
- **Android (Chrome):** menu ⋮ → **Add to Home screen / Install app**.
- **iPhone (Safari):** Share button → **Add to Home Screen**.

It installs with the COMPASS icon and opens full-screen like a native app.

---

## Notes

- **Demo accounts:** admin@compass.edu / admin123 · somayah@compass.edu / advisor123 · sara@compass.edu / student123
- **SECRET_KEY** is generated automatically by `render.yaml` (secure).
- **Data on the free plan is temporary** — Render's free filesystem resets on each redeploy,
  so the demo data re-seeds. For **durable data**, in `render.yaml` uncomment the `disk:` block
  and the `DB_PATH` env var (`/var/data/compass.db`), then redeploy. (A persistent disk needs a
  paid instance.)
- **Custom domain** (e.g. `compass-kau.com`): Render → your service → **Settings → Custom Domains**.
- **Free instances sleep** after inactivity and take ~30s to wake on the first request — fine for a pilot.

## For the official KAU rollout

For production use with real student data, deploy on **KAU IT infrastructure** with the university
domain and single sign-on, and switch SQLite → **PostgreSQL**. This repo is ready for that:
point `DB_PATH`/database config to the managed DB and run behind gunicorn as above.
