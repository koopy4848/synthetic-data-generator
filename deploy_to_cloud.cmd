docker build -t synthetic-data-generator .
docker tag synthetic-data-generator europe-central2-docker.pkg.dev/bigquery-demo-401007/sdg/sdg:latest
docker push europe-central2-docker.pkg.dev/bigquery-demo-401007/sdg/sdg:latest