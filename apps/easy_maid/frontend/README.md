# Easy Maid frontend (Vue + Frappe UI)

## Development

```bash
cd apps/easy_maid/frontend
npm install
npm run dev
```

## Build for Frappe assets

```bash
cd apps/easy_maid/frontend
npm run build
```

Build output is emitted to `apps/easy_maid/easy_maid/public/frontend` with stable filenames:

- `main.js`
- `main.css`

These are included via `hooks.py`:

- `/assets/easy_maid/frontend/main.js`
- `/assets/easy_maid/frontend/main.css`

## Auth strategy

- Route guards call `easy_maid.easy_maid.api.current_portal_role`.
- Guests are redirected to `/` and can use `/login` for ERPNext session auth.
- Development-only role simulation uses localStorage key `easymaid-role`.
