#!/bin/sh
# Wait for MinIO server to be healthy
/usr/bin/mc alias set local http://minio:9000 minioadmin minioadmin;
# Create the default bucket if it does not exist
/usr/bin/mc mb --ignore-existing local/fashion-media;
# Set policy to download for media access
/usr/bin/mc anonymous set download local/fashion-media;
exit 0;
