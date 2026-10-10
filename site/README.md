# MemoLint site

One static page. No build step, no dependencies, no framework.

## Deploy to Vercel

From inside this `site/` folder:

```bash
npx vercel --prod
```

First run asks a few questions. Accept the defaults: it detects a static site, and the
output directory is this folder.

Or without the CLI: go to vercel.com, New Project, and drag this folder onto the page.

## Local preview

```bash
python -m http.server 8080
```

Then open http://localhost:8080

## Editing

Everything lives in `index.html`: markup, styles and the two small scripts for the copy
buttons and the tabs. The colours are CSS variables at the top of the file and match the
demo video and thumbnail.

To change a command shown on the page, edit both the visible text inside `<pre>` and the
`data-copy` attribute on its Copy button, or the button will copy something different from
what the reader sees.
