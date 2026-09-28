# Artéum

A painting-sharing site: people sign up, post a painting (their own or a
famous one) with a written report, follow other artists, and like pieces.
Museum-inspired palette (beige / espresso / burgundy), a real light and dark
mode, and a three-column layout modeled on Substack's own (sidebar → feed →
suggestions).

## Run it in VS Code

1. Open this `arteum` folder in VS Code (the one that directly contains
   `app.py`).
2. Open a terminal and run:
   ```
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # macOS/Linux
   pip install -r requirements.txt
   python app.py
   ```
3. Open http://127.0.0.1:5000

**If you ran an earlier version of this project before:** delete the old
`arteum.db` file first — the database schema changed again (a new `repost`
table, and an `image_filename` column on messages), and SQLite won't add
these to an existing database on its own.

The site now opens on the **login page** for anyone not signed in — the
feed, Explore, profiles and painting pages all require an account. A demo
account is seeded on first run (Van Gogh's *The Starry Night*, with the full
report you sent, so you can see the "Read more" behavior):
- username: `mira`  ·  password: `password123`

To set your own profile photo: go to your profile page and click the small
✎ button on your avatar.

New in this version:
- **Repost** — every painting has a repost button (next to like). Reposting
  puts it in your own followers' feed and your profile's Posts tab, tagged
  "so-and-so reposted", the way retweets work. Someone reposting your
  painting also shows up on your Activity page.
- **Activity page** — a real notifications feed: likes, reposts, and new
  followers, newest first, with a small dot on the "Activity" nav item
  when there's something you haven't seen yet.
- **Search** — a search box at the top of the sidebar with live results
  as you type (people and paintings), plus a full `/search` results page.
  On phones, it collapses to a search icon in the top bar.
- **People to follow, mid-feed** — a horizontal row of suggested artists
  now appears after the second post in Home/Explore, similar to how
  Substack and X drop suggestions into the middle of the feed rather than
  only in a side rail.
- **Images in Messages** — the message box now has an attach button (📎);
  pick an image, see a preview, and send it with or without text. Received
  images show inline in the conversation.
- **Profile page redesign** — a cover strip, a bigger avatar, Posts / Likes
  / Following tabs, and a "Share a painting…" quick-composer on your own
  profile — closer to the profile layout you pointed to.
- **A real phone layout** — under ~640px wide, the sidebar becomes a
  compact top bar (icons only, horizontally scrollable if needed) instead
  of squeezing the full desktop sidebar into a narrow column, so the site
  is properly usable on a phone browser, not just resized-desktop.
- **New home headline** — "Fresh off the easel" instead of "Today's
  canvases" (translated too: "طازجة من المرسم"). Change it any time in
  `TRANSLATIONS["en"]["home_title"]` / `["ar"]["home_title"]` in `app.py`.
- **Settings / language** — a "Settings" page to switch the whole site's
  interface between English and Arabic (`app.py`'s `TRANSLATIONS` dict is
  where those strings live — add a key there and use `{{ t('your_key') }}`
  in a template to translate something new).
- **Many image formats** — the upload whitelist covers jpg, png, gif, webp,
  bmp, tiff, avif, heic and heif (SVG is blocked on purpose: an SVG opened
  directly can run scripts).
- **Sidebar spacing, actually fixed** — the real bug was a hardcoded
  `height: 100vh` on the sidebar and rail that forced them to stretch the
  full screen height even when their content was short. That's removed now;
  they simply hug their own content while staying sticky as you scroll.
- **Sharper logo** — the sidebar uses a tightly cropped version of your
  logo's "A" mark (`static/img/logo-mark.png`) instead of the whole
  logo+wordmark composition, so it stays legible at small sizes.

## Where things live

- `app.py` — models (`User`, `Painting`, `Like`, `Follow`, `Repost`,
  `Message`), auth routes (`/signup`, `/login`, `/logout`), the feed routes
  (`/`, `/explore`, `/gallery`, `/profile/<username>`), `/add` to post a
  painting, `/painting/<id>` for the full detail page, `/activity` for
  notifications, and `/search` + `/api/search` for the search box. The
  `build_feed_items()` helper is what merges original paintings and reposts
  into one, newest-first feed — every feed-like page (Home, Explore, My
  gallery, a profile's Posts tab) goes through it.
- `arteum.db` — created automatically on first run (SQLite). Delete it to
  start over with a clean, re-seeded database.
- `static/uploads/` — uploaded painting images land here.
- `static/img/logo.png` — the Artéum logo, used in the sidebar.
- `templates/` — `base.html` is the shared shell (sidebar, right rail, and
  the dark-mode toggle); `_painting_card.html` is the reusable feed card;
  `painting.html` is the full detail page; the rest are one page each.
- `static/css/style.css` — the whole visual system: beige background,
  burgundy as the one primary action color (the way Substack uses orange —
  it's on "Add a painting", "Follow", likes, and links), Original Surfer for
  headings, Amiri for Arabic report text, Lora for Latin-script reports, and
  a `[data-theme="dark"]` variant of every color for the dark mode toggle
  in the sidebar (saved to the browser's `localStorage`, so it's remembered
  across visits).

## Notes for going further

- This is set up for local use. Before putting it online: set a real,
  random `SECRET_KEY` in `app.py`, turn off `debug=True`, and swap SQLite
  for Postgres if you expect real traffic.
- Supported image types: jpg, png, gif, webp, bmp, tiff, avif, heic, heif
  — 12 MB max per upload.
- Paintings have **no frame** around them by request — just the image with
  soft rounded corners. If you ever want one back, that's a small addition
  to the `.artwork` rule in `style.css`.
- Report text is shown with `dir="auto"`, so Arabic and Latin reports both
  align correctly automatically depending on what was typed.

## Deploying it

See **DEPLOY.md** for step-by-step instructions (PythonAnywhere for a quick
test with friends; Render + Neon for something that scales), including what
was hardened for production. In short: set `ARTEUM_ENV=production` on the
server, and optionally `SECRET_KEY` and `DATABASE_URL` (a Postgres
connection string from Neon or Supabase — no code change needed).
