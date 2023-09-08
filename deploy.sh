gcloud config set run/region asia-northeast1

gcloud run deploy tabooo-api \
    --source . \
    --port=8080 \
    --allow-unauthenticated \
