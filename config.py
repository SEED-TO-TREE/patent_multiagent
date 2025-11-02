import os
from dotenv import load_dotenv

# .env 파일 자동 로드
load_dotenv()


class Config:
    """프로젝트 설정 관리 클래스"""

    # OpenAI 설정
    # ① 환경변수에서 API 키를 가져오되, 없으면 빈 문자열을 기본값으로 사용
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = "gpt-5-mini"
    MAX_TOKENS: int = 150

    # ② 현재 파일의 위치를 기준으로 프로젝트 루트 디렉토리를 설정
    ROOT_DIR: str = os.path.dirname(os.path.abspath(__file__))

    # KIPRIS API 설정
    KIPRIS_API_KEY: str = os.getenv("KIPRIS_API_KEY", "")
    KIPRIS_API_URL: str = "http://plus.kipris.or.kr/openapi/rest/patUtiModInfoSearchSevice/cpcSearchInfo"
    CPC_NUMBER: str = "G06N"  # CPC 번호 (AI/머신러닝 관련)
    TOTAL_PAGES: int = 1  # 수집할 총 페이지 수
    NUM_OF_ROWS: int = 30  # 한 페이지에 요청할 데이터 수
    CSV_PATH: str = "patent_data.csv"  # CSV 파일 경로

    # ③ API 호출을 효율적으로 하기 위한 배치 크기를 설정
    BATCH_SIZE: int = 10

    # ④ 특허를 분류할 카테고리 목록을 정의
    PATENT_CATEGORIES: list[str] = [
        "인공지능/머신러닝",
        "자율주행/로보틱스",
        "의료/건강",
        "이미지처리/비전",
        "자연어처리",
        "네트워크/보안",
        "하드웨어/센서",
        "기타",
    ]

    PATENT_PER_CATEGORY: int = 30  # 카테고리별 표시할 특허 수

    # ⑤ 출력 파일들을 저장할 디렉토리 설정
    OUTPUT_DIR: str = f"{ROOT_DIR}/outputs"

    # ⑥ 설정의 유효성을 검사하는 클래스 메서드
    @classmethod
    def validate(cls) -> bool:
        """설정 유효성 검사"""
        if not cls.OPENAI_API_KEY:
            print("OpenAI API 키가 설정되지 않았습니다.")
            print("환경변수 OPENAI_API_KEY를 설정하거나 실행 시 입력하세요.")
            return False
        return True
