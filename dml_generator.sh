#!/bin/bash

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "Файл .env не найден"
    exit 1
fi

OUTPUT_DIR="${OUTPUT_DIR:-./dml}"

mkdir -p "$OUTPUT_DIR"

export PGPASSWORD=$DB_PASSWORD

for table in users preferences photos match done_match user_interests; do
    pg_dump \
        -U $DB_USER \
        -d $DB_NAME \
        -h $DB_HOST \
        -p $DB_PORT \
        --data-only \
        --inserts \
        -t bot.$table \
        > "${OUTPUT_DIR}/${table}_dml.sql"
done

echo "Данные экспортированы в: $OUTPUT_DIR/"