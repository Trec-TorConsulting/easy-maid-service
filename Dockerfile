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

# Register the app in apps.txt. The base image's apps.txt has no trailing
# newline, so normalise with awk before appending to avoid concatenating onto
# the last entry (e.g. "erpnecteasy_maid").
RUN awk 'NF' /home/frappe/frappe-bench/sites/apps.txt > /tmp/apps.txt && \
    (grep -qxF 'easy_maid' /tmp/apps.txt || echo 'easy_maid' >> /tmp/apps.txt) && \
    mv /tmp/apps.txt /home/frappe/frappe-bench/sites/apps.txt && \
    echo "── apps.txt ──" && cat /home/frappe/frappe-bench/sites/apps.txt

# Link the app's public dir into the bench assets dir so /assets/easy_maid/*
# (including the prebuilt Vue frontend) resolves. `bench build` creates the
# per-app assets symlink and processes any bundles.
RUN bench build --app easy_maid

# ── Image metadata ──────────────────────────────────────────────────────────
LABEL org.opencontainers.image.title="Easy Maid Service Bench"
LABEL org.opencontainers.image.description="Frappe/ERPNext bench with the easy_maid app"
LABEL org.opencontainers.image.vendor="Trec-Tor Consulting"
LABEL org.opencontainers.image.source="https://github.com/Trec-TorConsulting/easy-maid-service"
LABEL org.opencontainers.image.version="0.0.1"
