from dataclasses import dataclass

from environs import Env

@dataclass
class TgBot:
    token: str # Токен для доступа к тг-боту
    admin_ids: list[int] # Список id администраторов

@dataclass
class PgManager:
    pg_link: str
    root_pass: str

@dataclass
class Config:
    tg_bot: TgBot
    pg_manager: PgManager

def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(
        tg_bot=TgBot(
            token=env('BOT_TOKEN'),
            admin_ids=list(map(int, env.list('ADMIN_IDS'))),
        ),
        pg_manager=PgManager(
            pg_link=env('PG_LINK'),
            root_pass=env('ROOT_PASS')
        )
    )