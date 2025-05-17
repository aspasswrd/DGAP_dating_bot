#!/bin/bash

PARENT_DIR="$(dirname "$(pwd)")"

export PYTHONPATH="${PYTHONPATH}:${PARENT_DIR}"
export QT_QPA_PLATFORM="xcb"

run_analysis() {
    local script_name=$1

    echo "Запуск $script_name..."
    python3 "${script_name}.py" 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "✅ $script_name выполнен успешно"
    else
        echo "❌ Ошибка при выполнении $script_name"
        exit 1
    fi
}

run_analysis "analyze_age_diff"
run_analysis "analyze_gender_ratio"
run_analysis "analyze_likes_matches"

echo "Все анализы завершены. Результаты сохранены в папке plots/"