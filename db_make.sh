#!/bin/bash
set -e

if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo "Файл .env не найден"
    exit 1
fi

export PGPASSWORD=$DB_PASSWORD

execute_sql() {
    local file=$1
    echo "Выполнение файла: $file"
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
        -q -v ON_ERROR_STOP=1 -f "$file" >/dev/null
}

execute_sql "ddl.sql"
execute_sql "dml/users_dml.sql"
execute_sql "dml/interests_dml.sql"
execute_sql "dml/user_interests_dml.sql"
execute_sql "dml/preferences_dml.sql"
execute_sql "dml/photos_dml.sql"
execute_sql "dml/match_dml.sql"
execute_sql "dml/done_match_dml.sql"
execute_sql "dml/my_profile_dml.sql"