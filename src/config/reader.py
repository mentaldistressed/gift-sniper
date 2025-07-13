import os 

from pydantic import BaseModel
from yaml import safe_load


class RedisConfig(BaseModel):
    host: str
    port: int

class Config(BaseModel):
    version: str  

    bot_token: str 
    parse_mode: str

    admin_url: str
    developer: str 
    owner: int
    split_tg: str

    vip_poll_interval: int
    default_poll_interval: int 
    bach_size: int

    vip_price: int

    redis: RedisConfig

class ConfigReader:
    def __init__(self, path: str = 'config.yaml'):
        if not os.path.exists(path):
            raise FileNotFoundError(f'Not found config for path: {path}')
        else:
            with open(path) as config_file:
                self.data = safe_load(config_file)

    def _load(self):
        return Config(**self.data)