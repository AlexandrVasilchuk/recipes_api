# Foodgram
URL: https://vsko.sytes.net/  
IP: 51.250.97.224

Данные администратора:  
username: root  
email: root@gmail.com  
password: admin  
---

## Описание проекта.
Позволяет пользователям сохранять рецепты, добавлять их в избранное. Подписываться на авторов. Автоматически создает список покупок из рецептов, которые вы хотите повторить!

Примеры запросов:  
Для неавторизованных пользователей работа с API доступна в режиме чтения, что-либо изменить или создать не получится.

```
GET /api/recipes/ - получить список всех рецептов.
GET /api/recipes/{id} - получение рецепта по id.
GET /api/ingredients/ - список всех ингрединетов, которые уже добавили в БД.
```

Для авторизованных пользователей добавляется функиционал добавления, обновления или полной замены объектов.

### Пример работы:

```
POST api/recipes/
{
  "ingredients": [
    {
      "id": 1123,
      "amount": 10
    }
  ],
  "tags": [
    1,
    2
  ],
  "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAgMAAABieywaAAAACVBMVEUAAAD///9fX1/S0ecCAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAACklEQVQImWNoAAAAggCByxOyYQAAAABJRU5ErkJggg==",
  "name": "string",
  "text": "string",
  "cooking_time": 1
}

```

### Как создать пользователя?

```
POST api/users/
В теле запроса указать:
{
  "email": "vpupkin@yandex.ru",
  "username": "vasya.pupkin",
  "first_name": "Вася",
  "last_name": "Пупкин",
  "password": "Qwerty123"
}

В случае валидности, получим ответ:
{
"email": "vpupkin@yandex.ru",
"id": 0,
"username": "vasya.pupkin",
"first_name": "Вася",
"last_name": "Пупкин"
}

```

### Как получить токен?

```
POST api/auth/token/login/
В теле запроса указать:
{
  "password": "string",
  "email": "string"
}
```

---
### Полная документация после запуска проекта доступна по ссылке:

___

# Как работать с репозиторием финального задания
1. Скопируйте репозиторий на локальный пк.
2. В корневой директории проекта создайте файл .env. 
3. Добавьте туда следующие параметры

```
ALLOWED_HOST - <разрешенные хосты через пробел>
SECRET_KEY - <ключ джанго>
POSTGRES_USER=<django_user> - имя пользователя
POSTGRES_PASSWORD=<mysecretpassword> - ваш пароль
POSTGRES_DB=django
DB_HOST=db
DB_PORT=5432
```

4. Выполните команду

```bash
docker compose up --build
```
## Технологии

[Python 3.9+][Python-url], [DRF 3.12+][Django-url], [Django 3.2+][Django-url]

## ⚠ Зависимости

> **Warning**:
> Для запуска требуются установленные зависимости:  
> ![Docker-badge]

---

<p style="text-align: center">
Автор:
<a href=" https://github.com/AlexandrVasilchuk">Васильчук Александр</a>
</p>

Студент когорты 20+.

### Контакты:

<a href="mailto:alexandrvsko@gmail.com">![Gmail-badge] <a/>
<a href="https://t.me/vsko_ico">![Telegram-badge] <a/>

[Gmail-badge]: https://img.shields.io/badge/Gmail-D14836?style=for-the-badge&logo=gmail&logoColor=white
[Telegram-badge]: https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white
[Python-url]: https://www.python.org/
[Django-url]: https://www.djangoproject.com/download/
[DRF-url]: https://pypi.org/project/djangorestframework/
[Docker-badge]: https://img.shields.io/badge/Docker-CI%2FCD-blue
[Docker-url]: https://www.docker.com/products/docker-desktop/