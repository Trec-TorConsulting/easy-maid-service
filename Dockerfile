# syntax=docker/dockerfile:1
#
# Easy Maid Service — Bench image
#
# Builds a Frappe/ERPNext bench image with the custom `easy_maid` app baked in,
# so every production pod runs identical app code and assets. Because all frappe
# workloads pull this single immutable image, it also eliminates the asset-hash
# drift caused by the rolling upstream `version-16` tag.
#
# Build & push (run from the repo root, MaidService/):
#   docker buildx build \
#     --platform linux/amd64,linux/arm64 \
#     -t 192.168.4.10:30500/easy-maid-service/bench:0.0.1 \
#     --push \
#     -f Dockerfile \
#     .
#
# Verify:
#   docker manifest inspect 192.168.4.10:30500/easy-maid-service/bench:0.0.1
#
FROM frappe/erpnext:version-16

# ── Install the custom app ──────────────────────────────────────────────────
# Copy only the runtime app package. The Vue frontend is already prebuilt and
# committed under easy_maid/public/frontend, so the frontend/ source dir (and its
# node_modules) is not needed at runtime.
COPY apps/easy_maid/easy_maid \
     /home/frappe/frappe-bench/apps/easy_maid/easy_maid
COPY apps/easy_maid/pyproject.toml \
     /home/frappe/frappe-bench/apps/easy_maid/pyproject.toml
COPY apps/easy_maid/license.txt \
     /home/frappe/frappe-bench/apps/easy_maid/license.txt
COPY apps/easy_maid/README.md \
     /home/frappe/frappe-bench/apps/easy_maid/README.md

# Install the app into the bench virtualenv (editable) so Frappe can import it.
RUN /home/frappe/frappe-bench/env/bin/pip install --no-cache-dir \
    -e /home/frappe/frappe-bench/apps/easy_maid

# ── Install the hrms app (Frappe HR + Payroll, separated from ERPNext v16) ────
# Salary Component, Salary Structure, Salary Slip, Payroll Entry, Shift Type,
# and Shift Assignment all live in frappe/hrms in ERPNext v16+.
RUN cd /home/frappe/frappe-bench && \
    bench get-app --branch version-16 https://github.com/frappe/hrms 2>&1

# Register the app in apps.txt. The base image's apps.txt has no trailing
# newline, so normalise with awk before appending to avoid concatenating onto
# the last entry (e.g. "erpnecteasy_maid").
RUN awk 'NF' /home/frappe/frappe-bench/sites/apps.txt > /tmp/apps.txt && \
    (grep -qxF 'hrms' /tmp/apps.txt || echo 'hrms' >> /tmp/apps.txt) && \
    (grep -qxF 'easy_maid' /tmp/apps.txt || echo 'easy_maid' >> /tmp/apps.txt) && \
    mv /tmp/apps.txt /home/frappe/frappe-bench/sites/apps.txt && \
    echo "── apps.txt ──" && cat /home/frappe/frappe-bench/sites/apps.txt

# NOTE: We deliberately do NOT run `bench build --app easy_maid` here.
# easy_maid's frontend is prebuilt/committed (easy_maid/public/frontend) and its
# public files are static, so it needs no esbuild bundling. Running
# `bench build --app easy_maid` would CREATE a real sites/assets/ dir baked into
# the image whose assets.json contains ONLY easy_maid's (empty) web-bundle map
# `{}`, wiping the frappe/erpnext mappings. The frappe-python `seed-sites`
# initContainer then copies that baked `{}` onto the shared PVC on every pod
# start, breaking every web bundle (login/website CSS+JS 404). Instead we leave
# the base image's pristine, complete assets at /home/frappe/frappe-bench/assets
# untouched; the site-init Job materializes them (plus /assets/easy_maid/*) onto
# the PVC via `cp -aL`.

# ── Multi-domain socketio (realtime) fix ────────────────────────────────────
# The stock nginx template pins the websocket `Origin` header to
# ${FRAPPE_SITE_NAME_HEADER} (our fixed site name, easymaid.trector.com). But
# Frappe's socketio `authenticate` middleware rejects a connection unless
# hostname(Origin) == hostname(Host). Because we serve a different public host
# (maidurday.com) through a fixed site header, that check fails with
# "Invalid origin" and realtime (live notifications, list refresh) breaks.
# Point `Origin` at the real incoming `$host` so it always matches `Host`.
# The template lives under the root-owned /templates dir, so patch it as root
# and drop back to the unprivileged frappe user afterwards.
USER root
RUN sed -i 's|Origin $proxy_x_forwarded_proto://${FRAPPE_SITE_NAME_HEADER}|Origin $proxy_x_forwarded_proto://$host|' \
    /templates/nginx/frappe.conf.template
USER frappe

# ── Image metadata ──────────────────────────────────────────────────────────
LABEL org.opencontainers.image.title="Easy Maid Service Bench"
LABEL org.opencontainers.image.description="Frappe/ERPNext bench with the easy_maid app"
LABEL org.opencontainers.image.vendor="Trec-Tor Consulting"
LABEL org.opencontainers.image.source="https://github.com/Trec-TorConsulting/easy-maid-service"
LABEL org.opencontainers.image.version="0.1.0"
