# Notes for working on this site

Joseph M. Ryan's research website: https://joseph-m-ryan.github.io (repo `joseph-m-ryan/joseph-m-ryan.github.io`). See `README.md` for how to add publications and projects.

## How it builds and deploys

- GitHub Pages' **classic build** from `main` (no Pages workflow): the `github-pages` gem, i.e. Jekyll 3.10 in `--safe` mode with only whitelisted plugins. No custom plugins and no Jekyll 4 features. Pushing to `main` deploys in about a minute.
- Check a change the way Pages builds it: `JEKYLL_ENV=production bundle exec jekyll build --safe`.
- On the user's Mac the system Ruby (2.6) is too old for the gems. Use the conda env `jekyll` (Ruby 3.3, set up 2026-10-12; gems in `vendor/bundle`): `conda activate jekyll`, and put `$CONDA_PREFIX/bin` first on `PATH` so `bundle` isn't `/usr/bin/bundle`.
- The user pushes straight to `main`; commit or push only when they ask.

## Design and code layout

- Custom design (Oct 2026) modeled on https://functions-lab.github.io (layout, IBM Plex fonts, year-grouped publications, badges, filters) and al-folio sites like https://yuanliu.group/publications/ (thumbnail + Abstract/arXiv/PDF/BibTeX buttons). Dark mode is the default.
- Styles: `assets/css/site.css` is plain CSS (no Sass) with color tokens on `:root` and `[data-theme="dark"]`. Scripts: `assets/js/site.js` (theme toggle, mobile menu, Abstract/BibTeX panels, copy, publication filters). No jQuery.
- Layouts: `default`, `home` (about.md), `publication`, `project`, `single`, `archive`. Publication pieces: `_includes/pub-entry.html`, `pub-links.html`, `pub-meta.html`, `pub-card.html`.
- The old academicpages Sass (`_sass/`, `assets/css/main.scss`) and JS (`assets/js/main.min.js`, `_main.js`), plus includes like `sidebar.html` and `author-profile.html`, are still in the repo but no longer used. They're safe to delete.

## Gotchas

- `_layouts/compress.html` collapses whitespace in production, so **inline `<script>` blocks must not use `//` comments** (everything ends up on one line). External JS files are unaffected.
- `base_path` is absolute (`site.url`), so built links point at the production URL. For local preview, `jekyll serve` (development env) overrides the URL; production-mode local builds need a `url:` override config.
- Publication thumbnails are 4:3 webp (720×540) cropped from square art; the full image is used on the paper page. The crop command is in `README.md`.
- The publication "abstracts" in front matter are short summaries (the newest one was written by Claude), not verbatim arXiv abstracts. The user may swap in the real ones.
- The home page's News and Talks sections (and `_data/news.yml`, `_data/talks.yml`) were removed on 2026-10-12; talks now live only in the CV.

## CV pipeline (don't edit `cv/` directly)

Overleaf → private repo `joseph-m-ryan/CV_github` → its `.github/workflows/notify-website.yml` sends a `repository_dispatch` (secret `WEBSITE_DISPATCH_TOKEN`) → this repo's `sync-cv.yml` subtree-pulls into `cv/` (secret `CV_REPO_TOKEN`) → `build-cv.yml` builds `files/cv.pdf` and `_includes/cv-generated.html`.

- `cv/` is a git subtree of `CV_github`; changes to the notify workflow must be made in `CV_github` itself.
- Both secrets hold the same **fine-grained** PAT (`cv-sync`, Contents read/write, scoped to `CV_github` and this repo), rotated from a classic PAT on 2026-08-16. If a classic PAT shows up again, treat it as a regression.
- The pipeline was verified end to end after the account rename (2026-10-08).

## History and open items

- **2026-10-08:** the GitHub account was renamed `joseph-ryan-quantum` → `joseph-m-ryan` (short names like josephryan/jmryan/josephmryan were taken). The old `joseph-ryan-quantum.github.io` now 404s because GitHub doesn't redirect Pages addresses.
- **Open:** bring the old address back as a redirect. The ready-made files and steps are in `tools/old-url-redirect/`; the user has to create the `joseph-ryan-quantum` org first.
- **Open:** update the website link on Google Scholar / ORCID / LinkedIn if they list it.
- **Open:** the user's new preprint (arXiv:2610.09047) isn't in the CV yet; that has to be added in Overleaf.
- **In progress:** the user would like to move the Noel Lab site (https://noellab.pratt.duke.edu, Pratt's Drupal 11 platform with the shared `engrlab` theme) to this Jekyll design on GitHub Pages. They're checking with the Pratt web admin and the PI (Crystal Noel) first. Nothing has been built yet; a lab version would need People, research areas, Join us, and lab-wide publications.
