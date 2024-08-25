from asyncpg_lite import DatabaseManager
from config_data.config import Config, load_config
from sqlalchemy import Integer, Boolean, ARRAY, BigInteger

# Загружаем конфиг в переменную config
config: Config = load_config()

# Создаем менеджер базы данных
pg_manager = DatabaseManager(db_url=config.pg_manager.pg_link, deletion_password=config.pg_manager.root_pass)


# Создаем таблицу пользователей
async def create_table_users(table_name='users'):
    async with pg_manager:
        columns = [
            {"name": "user_id", "type": BigInteger, "options": {"primary_key": True, "autoincrement": False}},
            {"name": "page", "type": Integer},
            {"name": "bookmarks", "type": ARRAY(Integer)},
            {"name": "user_state", "type": Boolean},
            {'name': "message_id", "type": Integer}
        ]

        await pg_manager.create_table(table_name=table_name, columns=columns)


# Функция получения всех записей по user_id
async def get_user_data(user_id: int, table_name='users'):
    async with pg_manager:
        user_info = await pg_manager.select_data(
            table_name=table_name,
            where_dict={'user_id': user_id},
            one_dict=True
        )
        if user_info:
            return user_info
        else:
            return None


# Функция добавления нового пользователя
async def insert_user(user_data: dict, table_name='users'):
    async with pg_manager:
        await pg_manager.insert_data_with_update(
            table_name=table_name,
            records_data=user_data,
            conflict_column='user_id'
        )


# Функция обновления данных пользователя по user_id
async def update_user_data(where: dict,update: dict,table_name='users'):
    async with pg_manager:
        await pg_manager.update_data(
            table_name=table_name,
            where_dict=where,
            update_dict=update
        )
