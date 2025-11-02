import requests
import pandas as pd
import xml.etree.ElementTree as ET
import os
from dotenv import load_dotenv

# .env 파일 자동 로드
load_dotenv()

# API 엔드포인트
url = 'http://plus.kipris.or.kr/openapi/rest/patUtiModInfoSearchSevice/cpcSearchInfo'

# 필요한 데이터를 저장할 리스트
patent_data = []
total_requests = 1  # 요청할 총 페이지 수 (예: 100개를 위해 4페이지 요청)

KIPRIS_API_KEY: str = os.getenv("KIPRIS_API_KEY", "")

# 여러 페이지 요청
for page in range(1, total_requests + 1):
    params = {
        'cpcNumber': 'G06N',  # CPC 번호를 설정
        'accessKey': KIPRIS_API_KEY,  # 실제 API 키 입력
        'pageNo': page,    # 요청할 페이지 번호
        'numOfRows': 30    # 한 페이지에 요청할 데이터 수 (기본 30개)
    }

    # API 요청
    response = requests.get(url, params=params)

    # 응답 확인
    if response.status_code == 200:
        # XML 데이터를 파싱
        root = ET.fromstring(response.content)
        
        # XML에서 각 'PatentUtilityInfo' 태그를 찾음
        for item in root.findall('.//PatentUtilityInfo'):
            application_number = item.find('ApplicationNumber').text if item.find('ApplicationNumber') is not None else 'N/A'
            abstract = item.find('Abstract').text if item.find('Abstract') is not None else 'N/A'
            invention_name = item.find('InventionName').text if item.find('InventionName') is not None else 'N/A'
            registration_number = item.find('RegistrationNumber').text if item.find('RegistrationNumber') is not None else 'N/A'

            # 각 특허 데이터를 딕셔너리로 저장
            patent_data.append({
                'ApplicationNumber': application_number,
                'Registration Number': registration_number,         
                'Invention Name': invention_name,
                'Abstract': abstract,
            })
    else:
        print(f"Failed to fetch data for page {page}: {response.status_code}")

# 리스트를 데이터프레임으로 변환
df = pd.DataFrame(patent_data)

# 데이터프레임 출력
print(df)

# CSV 파일로 저장
df.to_csv("patent_data.csv", index=False, encoding="utf-8-sig")
# 출처: https://lnylnylnylny.tistory.com/46 [곤뷰 일기장:티스토리]