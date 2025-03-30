#!/bin/bash
set -e

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "Файл .env не найден"
    exit 1
fi

export PGPASSWORD=$DB_PASSWORD

mkdir -p csv

TABLES=$(psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -t -c \
    "SELECT table_name FROM information_schema.tables
     WHERE table_schema = 'bot' AND table_type = 'BASE TABLE'")

for TABLE in $TABLES; do
    echo "Экспорт таблицы: bot.$TABLE"

    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c \
        "\COPY (SELECT * FROM bot.$TABLE) TO 'csv/${TABLE}.csv' WITH (FORMAT CSV, HEADER, DELIMITER ',', ENCODING 'UTF8')"
done

echo "Все таблицы из схемы bot экспортированы в папку csv/"