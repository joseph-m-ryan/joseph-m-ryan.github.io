# Redirect for the old site address

The GitHub account was renamed from `joseph-ryan-quantum` to `joseph-m-ryan` on 2026-10-08, and GitHub does not redirect old `*.github.io` addresses. These files bring the old address back as a redirect, keeping the page path (so an old link to a paper lands on the same paper).

To use them:

1. Create a free GitHub organization named `joseph-ryan-quantum` (this also stops anyone else claiming the old name).
2. In it, create a public repo named `joseph-ryan-quantum.github.io`.
3. Copy `index.html` and `404.html` from this folder into that repo and push. GitHub Pages serves `404.html` for every unknown path, which is what makes deep links work.

This folder is excluded from the main site build in `_config.yml`.
