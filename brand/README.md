# Easy Maid Service — Brand Assets (starting point)

> ⚠️ These are **placeholder starter assets** generated to unblock development.
> Replace with final artwork before launch.

## Palette

| Token | Hex | Use |
| --- | --- | --- |
| Teal (top) | `#2DD4BF` | Badge gradient top, highlights |
| Teal (deep) | `#0D9488` | Badge gradient bottom, primary text/brand |
| Amber | `#FACC15` | Sparkle accent, calls to action |
| Slate | `#0F172A` | Body text, "SERVICE" wordmark |
| White | `#FFFFFF` | On-teal text, monogram |

## Files

| File | Size | Purpose |
| --- | --- | --- |
| `logo-mark.svg` | vector | Scalable app/badge mark (preferred) |
| `favicon.svg` | vector | Scalable favicon |
| `logo-mark.png` | 512 | Raster mark |
| `logo-full.png` | wordmark | Mark + "Easy Maid Service" lockup |
| `icon-192.png` / `icon-512.png` | 192 / 512 | PWA / web app manifest icons |
| `apple-touch-icon.png` | 180 | iOS home-screen icon |
| `favicon.ico` | 16/32/48/64 | Browser favicon |

## Regenerate rasters

```bash
# from repo root
python3 -m venv .venv-assets && .venv-assets/bin/pip install pillow
cd brand && ../.venv-assets/bin/python generate_assets.py
```

Fonts fall back to system Arial/Helvetica Bold. For pixel-consistent output across
machines, swap in a bundled font file inside `generate_assets.py`.
