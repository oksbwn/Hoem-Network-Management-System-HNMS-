from pydantic import BaseModel

class ConfigItem(BaseModel):
    key: str
    value: str

class ConfigUpdate(BaseModel):
    value: str
