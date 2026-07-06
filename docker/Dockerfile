# Sandbox image for skillproof: runs agent-generated code and graders.
# Keep in sync with packages.txt (quoted to Codex when authoring benchmarks).
FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
        bash coreutils git jq ripgrep poppler-utils curl ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
        pytest==8.3.4 \
        numpy==2.2.1 \
        pandas==2.2.3 \
        pypdf==5.1.0 \
        reportlab==4.2.5 \
        openpyxl==3.1.5 \
        python-docx==1.1.2 \
        pyyaml==6.0.2 \
        pillow==11.1.0 \
        beautifulsoup4==4.12.3 \
        lxml==5.3.0 \
        requests==2.32.3

RUN useradd -m -u 1001 agent && mkdir -p /workspace /skill /grader \
    && chown agent:agent /workspace

ENV TZ=UTC LC_ALL=C.UTF-8 LANG=C.UTF-8 PYTHONHASHSEED=0 SOURCE_DATE_EPOCH=0
USER agent
WORKDIR /workspace
