# joseph-ryan-quantum.github.io

Joseph M. Ryan's research website, built with [Jekyll](https://jekyllrb.com/) and hosted on GitHub Pages. It started from the [academicpages](https://github.com/academicpages/academicpages.github.io) template; the layouts and styles have since been replaced with a custom design (`assets/css/site.css`, `assets/js/site.js`).

## Editing content

- **Home page** (bio, interests, profile card links, "New preprint" banner): `_pages/about.md`
- **News** and **Talks** on the home page: `_data/news.yml`, `_data/talks.yml`
- **Publications**: one Markdown file per paper in `_publications/` (see below)
- **Projects**: one Markdown file per project in `_portfolio/`
- **CV**: generated from `cv/main.tex` (synced from Overleaf) into `_includes/cv-generated.html` and `files/cv.pdf`
- **Site-wide settings** (name, email, profile links): `_config.yml`
- **Nav bar**: `_data/navigation.yml`
- **Images**: `images/`; publication art goes in `images/publications/`

Push to `main` and GitHub Pages rebuilds the site within a minute or two.

## Adding a publication

Create `_publications/YYYY-MM-DD-short-name.md`. Everything lives in the front matter:

```yaml
---
title: "Paper title"
collection: publications
category: preprints            # or manuscripts (journal article); see publication_category in _config.yml
permalink: /publication/YYYY-MM-DD-short-name
date: YYYY-MM-DD               # sets the order and the year heading
authors: "Joseph M. Ryan, Co Author, Another Author"   # your name is bolded automatically
venue: "arXiv:XXXX.XXXXX [quant-ph]"                    # or e.g. "Physical Review Research 8, L022025"
venue_short: "arXiv"           # badge text, e.g. PRR, PRL, arXiv
excerpt: "One sentence for the home-page card and link previews."
abstract: >-
  Shown by the Abstract button and on the paper's own page.
arxiv: "XXXX.XXXXX"            # adds arXiv + PDF buttons
doi: "10.xxxx/xxxxx"           # optional
paperurl: "https://..."        # optional publisher page (Journal button)
pdf: "https://..."             # optional; defaults to the arXiv PDF
highlight: "Featured in ..."   # optional star line; add highlight_url to link it
thumbnail: /images/publications/name-thumb.webp   # 4:3 image for lists and cards
image: /images/publications/name.webp             # full image for the paper page
image_alt: "Describe the image."
projects: [quantum-fptds]      # optional; lists the paper on that project's page
bibtex: |
  @misc{key,
    title = {...},
    ...
  }
---
```

To make a 4:3 thumbnail from a square image with ImageMagick:

```bash
convert name.webp -crop 1254x940+0+157 +repage -resize 720x540 -quality 82 name-thumb.webp
```

## Local preview (optional)

Requires Ruby + Bundler:

```bash
bundle install
bundle exec jekyll serve
```

Then open http://localhost:4000.
