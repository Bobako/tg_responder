# tg_responder
Многофункциональный автоответчик для телеграм.

Версия 2.

## Запуск (для windows)
1. Скачать и распаковать проект (кнопка code -> download zip)
2. Запускать main.exe из папки executables/windows

## Установка (из исходников)
1. Файл зависимостей сконфигурирован под python3.10, поэтому рекомендую обновиться до этой версии. При этом убедитесь, что можете вызвать pip (на windows для этого отметьте флажок add python tp path при уставноке)
2. Скачать и распаковать проект (кнопка code -> download zip)
3. Перейти в директорию с проектом и запустить коммандную строку (на windows для этого введите cmd в строку пути в проводнике)
4. Запустить команду pip install -r requirments.txt
5. Запускать программу через файл main.py в директории с проектом.

### Настройка
Настройка некоторых параметров (например, ключ приложения для API телеграма) производится с помощью файла config.ini в корне проекта.
База данных храниться в директории app.

Соответственно, если использовать приложения из готовых исполняемых файлов, под корнем проекта следует понимать папку, где лежит main.exe.


