"""
Точка входа в приложение.
Запуск: python run.py
"""
from app import create_app

# Создаем приложение с конфигурацией по умолчанию
app = create_app()

if __name__ == '__main__':
    # Запускаем сервер на порту 5000
    app.run(debug=True, host='127.0.0.1', port=5000)