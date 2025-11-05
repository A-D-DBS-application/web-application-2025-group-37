[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/DxqGQVx4)

# OpWielekes – web app

## Home page images (customize)

You can use your own photos on the home page. Put them in:

```
static/img/home/
```

Use these filenames (or update the references in `templates/index.html`):

- Collage: `collage-1.jpg`, `collage-2.jpg`, `collage-3.jpg`, `collage-4.jpg`
- Carousel: `slide-1.jpg`, `slide-2.jpg`, `slide-3.jpg`

If a given file exists, it is used; otherwise a fallback Unsplash image is shown. This is done via the helper `static_or(filename, fallbackUrl)`.

Recommended sizes:

- Collage: ~800x600 (4:3)
- Carousel: ~1600x900 (16:9)

Tip: optimize images (JPEG or WEBP) to keep the page fast.
