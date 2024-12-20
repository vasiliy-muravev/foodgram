# Foodgram - сервис для обмена рецептами.

[![Python](https://img.shields.io/badge/Python-3776AB?style=plastic&logo=python&logoColor=092E20&labelColor=white
)](https://www.python.org/) [![Django](https://img.shields.io/badge/django-822e0d?style=plastic&logo=django&logoColor=092E20&labelColor=white
)](https://www.djangoproject.com/) [![Django REST Framework](https://img.shields.io/badge/-Django_REST_framework-DC143C?style=red
)](https://www.django-rest-framework.org/)

https://foodgram.vasiliymuravev.ru/recipes - демо версия проекта

Что умеет проект:

- Создавать, просматривать, редактировать и удалять рецепты.
- Добавлять рецепты в избранное
- Подписываться на других пользователей
- Создавать список покупок.

Проект интересен тем что полностью настроено "непрерывное развертывание" CI/CD
[https://github.com/vasiliy-muravev/foodgram/actions ](https://github.com/vasiliy-muravev/foodgram/actions) - описаны
Actions для Workflow
В момент отправки кода в репозиторий (событие git push) запускается цепочка действий по деплою. Обычно эти рутинные
действия выполняет разработчик, инструменты для автоматизации решают эту задачу.
В этом файле описаны
jobs [https://github.com/vasiliy-muravev/foodgram/blob/main/.github/workflows/main.yml](https://github.com/vasiliy-muravev/foodgram/blob/main/.github/workflows/main.yml)
В момент срабатывания события происходит следующее:

1. Выполняются тесты по беку
3. Пересобираются образы для контейнера
4. Образы отправляются в хранилище dockerhub
5. Бот заходит на сервер, отправляет команды вытянуть новые образы
6. Перезапускает все контейнеры
7. Выполняет миграции и сбор статики
8. Копирует статику в нужные папки
9. Отправляет через телеграм бот сообщение об успешном деплое

### Стэк используемых технологий

- Django
- DjangoRestFramework
- Docker
- Nginx
- Postgres

### Установка

1. Клонируйте репозиторий на свой компьютер:

    ```bash
    git clone git@github.com:vasiliy-muravev/foodgram.git
    ```
    ```bash
    cd foodgram
    ```
2. Создайте файл .env и заполните его своими данными. Перечень данных указан в корневой директории проекта в файле
   .env.example.

### Создание Docker-образов

1. Замените username на ваш логин на DockerHub:

   ```bash
   cd frontend
   docker build -t username/foodgram_frontend .
   cd ../backend
   docker build -t username/foodgram_backend .
   cd ../nginx
   docker build -t username/foodgram_gateway . 
   ```

2. Загрузите образы на DockerHub:

    ```bash
    docker push username/foodgram_frontend
    docker push username/foodgram_backend
    docker push username/foodgram_gateway
    ```

### Деплой на сервере

1. Подключитесь к удаленному серверу

    ```bash
    ssh -i путь_до_файла_с_SSH_ключом/название_файла_с_SSH_ключом имя_пользователя@ip_адрес_сервера 
    ```

2. Создайте на сервере директорию foodgram через терминал

    ```bash
    mkdir foodgram
    ```

3. Установка docker compose на сервер:

    ```bash
    sudo apt update
    sudo apt install curl
    curl -fSL https://get.docker.com -o get-docker.sh
    sudo sh ./get-docker.sh
    sudo apt-get install docker-compose-plugin
    ```

4. В директорию foodgram/ скопируйте файлы docker-compose.production.yml и .env:

    ```bash
    scp -i path_to_SSH/SSH_name docker-compose.production.yml username@server_ip:/home/username/foodgram/docker-compose.production.yml
    * ath_to_SSH — путь к файлу с SSH-ключом;
    * SSH_name — имя файла с SSH-ключом (без расширения);
    * username — ваше имя пользователя на сервере;
    * server_ip — IP вашего сервера.
    ```

5. Запустите docker compose в режиме демона:

    ```bash
    sudo docker compose -f docker-compose.production.yml up -d
    ```

6. Выполните миграции, соберите статические файлы бэкенда и скопируйте их в /backend_static/static/:

    ```bash
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
    sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
    sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
    ```

7. На сервере в редакторе nano откройте конфиг Nginx:

    ```bash
    sudo nano /etc/nginx/sites-enabled/default
    ```

8. Измените настройки location в секции server:

    ```bash
    location / {
        proxy_set_header Host $http_host;
        proxy_pass http://127.0.0.1:8080;
    }
    ```

9. Проверьте работоспособность конфига Nginx:

    ```bash
    sudo nginx -t
    ```
   Если ответ в терминале такой, значит, ошибок нет:
    ```bash
    nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
    nginx: configuration file /etc/nginx/nginx.conf test is successful
    ```

10. Перезапускаем Nginx
    ```bash
    sudo service nginx reload
    ```

### Настройка CI/CD

1. Файл workflow уже написан. Он находится в директории

    ```bash
    foodgram/.github/workflows/main.yml
    ```

2. Для адаптации его на своем сервере добавьте секреты в GitHub Actions:

    ```bash
    DOCKER_USERNAME                # имя пользователя в DockerHub
    DOCKER_PASSWORD                # пароль пользователя в DockerHub
    HOST                           # ip_address сервера
    USER                           # имя пользователя
    SSH_KEY                        # приватный ssh-ключ (cat ~/.ssh/id_rsa)
    SSH_PASSPHRASE                 # кодовая фраза (пароль) для ssh-ключа

    TELEGRAM_TO                    # id телеграм-аккаунта (можно узнать у @userinfobot, команда /start)
    TELEGRAM_TOKEN                 # токен бота (получить токен можно у @BotFather, /token, имя бота)
    ```

### Полезные команды
```
python -m flake8 .
isort --resolve-all-configs .
../postman_collection/clear_db.sh
```

### Автор проекта

**Муравьев Василий** 