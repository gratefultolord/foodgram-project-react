# Проект Foodgram
[![Main Foodgram Workflow](https://github.com/gratefultolord/foodgram-project-react/actions/workflows/main.yml/badge.svg)](https://github.com/gratefultolord/foodgram-project-react/actions/workflows/main.yml)
***
Продуктовый помощник. Включает в себя функции создания рецептов, сохранения их в избранное, добавления в корзину покупок, которую можно скачать в формате txt. Также есть возможность подписки на других авторов.
***
Адрес: ([https://fooddotgram.ddns.net](https://fooddotgram.ddns.net/recipes))

## Использованные технологии:
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django REST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray) 
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Gunicorn](https://img.shields.io/badge/gunicorn-%298729.svg?style=for-the-badge&logo=gunicorn&logoColor=white)
![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white)
![Postgresql](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)
[![Yandex.Cloud](https://img.shields.io/badge/-Yandex.Cloud-464646?style=flat-square&logo=Yandex.Cloud)](https://cloud.yandex.ru/)
## Подготовка и запуск проекта
### Клонировать репозиторий
- Клонировать репозиторий:
```
git clone git@github.com:gratefultolord/foodgram-project-react.git
```

- Установить на сервере Docker, Docker Compose:

```
sudo apt install curl                                   # установка утилиты для скачивания файлов
curl -fsSL https://get.docker.com -o get-docker.sh      # скачать скрипт для установки
sh get-docker.sh                                        # запуск скрипта
sudo apt-get install docker-compose-plugin              # последняя версия docker compose
```

- Скопировать на сервер файлы docker-compose.yml, nginx.conf из папки infra (команды выполнять находясь в папке infra):

```
scp docker-compose.yml nginx.conf username@IP:/home/username/   # username - имя пользователя на сервере
                                                                # IP - публичный IP сервера
```

- Для работы с GitHub Actions необходимо в репозитории в разделе Secrets > Actions создать переменные окружения:
```
SECRET_KEY              # секретный ключ Django проекта
DOCKER_PASSWORD         # пароль от Docker Hub
DOCKER_USERNAME         # логин Docker Hub
HOST                    # публичный IP сервера
USER                    # имя пользователя на сервере
PASSPHRASE              # *если ssh-ключ защищен паролем
SSH_KEY                 # приватный ssh-ключ
TELEGRAM_TO             # ID телеграм-аккаунта для посылки сообщения
TELEGRAM_TOKEN          # токен бота, посылающего сообщение

DB_ENGINE               # django.db.backends.postgresql
POSTGRES_DB             # postgres
POSTGRES_USER           # postgres
POSTGRES_PASSWORD       # postgres
DB_HOST                 # db
DB_PORT                 # 5432 (порт по умолчанию)
```

- Создать и запустить контейнеры Docker, выполнить команду на сервере
*(версии команд "docker compose" или "docker-compose" отличаются в зависимости от установленной версии Docker Compose):*
```
sudo docker compose up -d
```

- После успешной сборки выполнить миграции:
```
sudo docker compose exec backend python manage.py migrate
```

- Создать суперпользователя:
```
sudo docker compose exec backend python manage.py createsuperuser
```

- Собрать статику:
```
sudo docker compose exec backend python manage.py collectstatic --noinput
```

- Наполнить базу данных тегами и ингредиентами:
```
sudo docker compose exec backend python manage.py create_tags
sudo docker compose exec backend python manage.py import_ingredients
```

- Для остановки контейнеров Docker:
```
sudo docker compose down -v      # с их удалением
sudo docker compose stop         # без удаления
```

### После каждого обновления репозитория (push в ветку master) будет происходить:

1. Проверка кода на соответствие стандарту PEP8 (с помощью пакета flake8)
2. Сборка и доставка докер-образов frontend и backend на Docker Hub
3. Разворачивание проекта на удаленном сервере
4. Отправка сообщения в Telegram в случае успеха

### Запуск проекта на локальной машине:

- Клонировать репозиторий:
```
git clone git@github.com:gratefultolord/foodgram-project-react.git
```

- В директории infra создать файл .env и заполнить своими данными по аналогии с example.env:
```
DB_ENGINE=django.db.postgresql
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=secretpassword
POSTGRES_DB=foodgram
DB_HOST=127.0.0.1
DB_PORT=5432
DEBUG=False
SECRET_KEY='секретный ключ Django'
```

- Создать и запустить контейнеры Docker, последовательно выполнить команды по созданию миграций, сбору статики, 
созданию суперпользователя, как указано выше.
```
docker-compose up -d
```
```
- После запуска проект будут доступен по адресу: [http://localhost/](http://localhost/)
```

### Автор:

Каримов Шукурилло
