# Template environment — replace. Self-contained per-task image; Harbor builds it
# and drops the agent inside. Bake task inputs in via COPY.
#
# RULES (this project):
# - NO environment/skills/ — skills are injected per arm by the run harness; a
#   baked-in skill would leak into the without-skill baseline.
# - Keep deterministic: pin versions, no network at agent time unless task.md
#   declares network_mode: public for a domain-justified reason.
FROM python:3.13-slim

WORKDIR /root
# COPY input/ /root/input/
