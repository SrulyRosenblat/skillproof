# Self-contained task environment for building a PowerPoint deck from scratch.
# No pre-existing input document is needed for this task, only the pinned
# libraries for creating and inspecting a .pptx package. No skills/ here.
FROM python:3.12-slim

RUN pip install --no-cache-dir \
        pytest==8.3.4 \
        python-pptx==1.0.2 \
        pillow==11.1.0 \
        lxml==5.3.0

WORKDIR /workspace
