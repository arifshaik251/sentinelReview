#!/usr/bin/env bash
# Azure App Service (Linux) startup script for Streamlit.
# Azure forwards external traffic to the port defined in $PORT (default 8000).
python -m streamlit run app/main.py \
  --server.port=${PORT:-8000} \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --server.enableCORS=false \
  --server.enableXsrfProtection=false
