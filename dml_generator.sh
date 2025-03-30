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

    awk '
        BEGIN {
            first = 1;
            print "INSERT INTO bot.'$table' VALUES";
        }
        /^INSERT/ {
            sub(/^INSERT INTO [^ ]+ VALUES /, "");
            gsub(/[);]/, "");
            if (first) {
                printf "    %s", $0;
                first = 0;
            } else {
                printf "),\n    %s", $0;
            }
        }
        END {
            if (!first) print ");\n";
        }
    ' "${OUTPUT_DIR}/${table}_dml.sql" > "${OUTPUT_DIR}/${table}_dml.formatted.sql"

    sed -i.bak -e '$s/,$/;/' "${OUTPUT_DIR}/${table}_dml.formatted.sql"
    rm -f "${OUTPUT_DIR}/${table}_dml.formatted.sql.bak"

    mv "${OUTPUT_DIR}/${table}_dml.formatted.sql" "${OUTPUT_DIR}/${table}_dml.sql"
done

echo "Данные экспортированы в: $OUTPUT_DIR/"
