# Deploying Artéum so people can test it

Two paths. **Path A (PythonAnywhere) is recommended for a test run**: its
disk is persistent, so your database *and* uploaded paintings survive
restarts with zero extra services.

---

## Path A — PythonAnywhere (free, easiest)

1. Create a free account at pythonanywhere.com. Your username becomes your
   site address: `https://YOURUSERNAME.pythonanywhere.com`
2. **Files** tab → upload `arteum.zip` into your home folder.
3. **Consoles** tab → start a **Bash** console and run:
   ```
   unzip arteum.zip
   cd arteum
   python3.11 -m venv ~/venv
   source ~/venv/bin/activate
   pip install -r requirements.txt
   ```
   (Any Python 3.11+ works — just use the same version in step 4.)
4. **Web** tab → *Add a new web app* → *Manual configuration* → pick the
   same Python version. Then set:
   - **Virtualenv:** `/home/YOURUSERNAME/venv`
   - **WSGI configuration file:** click the link, delete everything, and
     paste the contents of `pythonanywhere_wsgi_snippet.py` (change
     `YOURUSERNAME`).
   - **Static files:** URL `/static/` → Directory
     `/home/YOURUSERNAME/arteum/static` (makes images load faster and saves
     your free CPU allowance).
5. Click the green **Reload** button, then open your site address. You
   should land on the login page — create the first account.

Things to know about the free plan:
- It has a small daily CPU allowance (about 100 CPU-seconds) — plenty for a
  handful of testers, not for a crowd.
- Free web apps expire if you don't renew them: log in now and then and use
  the extend button on the Web tab.
- To update the site later: upload new files (or a new zip), then Reload.

---

## Path B — Render + Neon (scales better, needs GitHub)

1. Put the project on GitHub (the included `.gitignore` keeps the database
   and secret key out).
2. **Neon** (neon.tech): create a free project and copy its connection
   string (`postgresql://…`).
3. **Render** (render.com): *New → Web Service* from your repo, then:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
   - Environment variables:
     - `ARTEUM_ENV` = `production`
     - `SECRET_KEY` = a long random string
     - `DATABASE_URL` = the Neon connection string

**Important caveat:** Render's free web service has a temporary disk, so
uploaded paintings and avatars are lost when it restarts or redeploys (the
database is fine — it's on Neon). Free instances also go to sleep when
idle, so the first visit after a quiet spell is slow. To keep images, either
add a paid persistent disk mounted at `static/uploads`, or move uploads to
cloud storage such as Cloudinary (ask and I'll add that).

---

## Before you share the link

- Tell testers this is a test site: there is no email verification or
  password reset yet, and no rate limiting — fine for friends, not yet for
  the open internet.
- There is **no demo account** in production (the `mira` / `password123`
  seed only runs locally), so nobody can log in with a known password.
- Back up `arteum.db` and `static/uploads/` if the test data matters.

## What was hardened for deployment

- `SECRET_KEY` comes from the environment (or a random key saved to
  `.secret_key`) instead of being hard-coded; debug mode is off in
  production; session cookies are HTTPS-only and `SameSite=Lax`.
- `DATABASE_URL` switches from SQLite to Postgres with no code change.
- Tables are created on startup, so it works under gunicorn / a WSGI host.
- Login only redirects to pages on this site (no open redirect).
- Usernames are limited to letters, numbers, dots, dashes, underscores
  (3–30 chars); passwords need at least 6 characters.
- SVG uploads are no longer accepted (an SVG opened directly can run
  scripts); search results are HTML-escaped.
- `/healthz` returns `ok` for hosting health checks.
