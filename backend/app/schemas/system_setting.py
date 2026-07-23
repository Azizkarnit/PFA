from pydantic import BaseModel

class SystemSettingsUpdate(BaseModel):
    code_expiration: int
    max_signin_attempts: int
    lock_duration: int
    password_only_duration: int
    default_language: str
    email_provider: str

class SystemSettingsResponse(SystemSettingsUpdate):
    pass
