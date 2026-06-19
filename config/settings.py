from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 공공데이터포털 - 보호수 현황 API
    PUBLIC_DATA_API_KEY: str = ""

    # 카카오 REST API - 지오코딩 (주소→좌표)
    KAKAO_REST_API_KEY: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
