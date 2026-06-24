# TODO

## 1) Fix Render 400 Bad Request
- [ ] Update `config/settings.py` so `ALLOWED_HOSTS` fully comes from env var (no localhost-only default in production).
- [ ] Optionally set `DEBUG` default to False when running on Render.
- [ ] Redeploy and validate `GET /` and `/favicon.ico` return non-400.

