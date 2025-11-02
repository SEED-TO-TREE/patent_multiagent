import requests
import pandas as pd
import xml.etree.ElementTree as ET
import os
from typing import Optional
from dotenv import load_dotenv

from state import PatentState
from config import Config


class PatentCollectorAgent:
    """KIPRIS API를 사용하여 특허 데이터를 수집하는 에이전트"""

    def __init__(self):
        self.name = "Patent Collector"
        self.url = 'http://plus.kipris.or.kr/openapi/rest/patUtiModInfoSearchSevice/cpcSearchInfo'
        load_dotenv()
        self.api_key = os.getenv("KIPRIS_API_KEY", "")

    def load_from_csv(self, csv_path: str = "patent_data.csv") -> list[dict[str, Optional[str]]]:
        """CSV 파일에서 특허 데이터를 로드합니다."""
        try:
            df = pd.read_csv(csv_path, encoding="utf-8-sig")
            patent_data = []
            
            for _, row in df.iterrows():
                patent_data.append({
                    'ApplicationNumber': str(row.get('ApplicationNumber', 'N/A')),
                    'RegistrationNumber': str(row.get('Registration Number', 'N/A')) if pd.notna(row.get('Registration Number')) else 'N/A',
                    'InventionName': str(row.get('Invention Name', 'N/A')),
                    'Abstract': str(row.get('Abstract', 'N/A')),
                })
            
            return patent_data
        except Exception as e:
            print(f"CSV 파일 로드 중 오류 발생: {e}")
            return []

    def collect_from_api(self, cpc_number: str = 'G06N', total_pages: int = 1, num_of_rows: int = 30) -> list[dict[str, Optional[str]]]:
        """KIPRIS API를 사용하여 특허 데이터를 수집합니다."""
        patent_data = []
        
        if not self.api_key:
            print("KIPRIS_API_KEY가 설정되지 않았습니다.")
            return []

        for page in range(1, total_pages + 1):
            params = {
                'cpcNumber': cpc_number,
                'accessKey': self.api_key,
                'pageNo': page,
                'numOfRows': num_of_rows
            }

            try:
                response = requests.get(self.url, params=params)
                
                if response.status_code == 200:
                    root = ET.fromstring(response.content)
                    
                    for item in root.findall('.//PatentUtilityInfo'):
                        application_number = item.find('ApplicationNumber').text if item.find('ApplicationNumber') is not None else 'N/A'
                        abstract = item.find('Abstract').text if item.find('Abstract') is not None else 'N/A'
                        invention_name = item.find('InventionName').text if item.find('InventionName') is not None else 'N/A'
                        registration_number = item.find('RegistrationNumber').text if item.find('RegistrationNumber') is not None else 'N/A'

                        patent_data.append({
                            'ApplicationNumber': application_number,
                            'RegistrationNumber': registration_number,
                            'InventionName': invention_name,
                            'Abstract': abstract,
                        })
                else:
                    print(f"API 요청 실패 (페이지 {page}): {response.status_code}")
                    
            except Exception as e:
                print(f"API 요청 중 오류 발생 (페이지 {page}): {e}")

        return patent_data

    def collect_patents(self, state: PatentState) -> PatentState:
        """특허 데이터를 수집하고 상태를 업데이트합니다."""
        print("--- 특허 데이터 수집 시작 ---")

        try:
            # CSV 파일에서 데이터 로드 시도
            if os.path.exists("patent_data.csv"):
                print("CSV 파일에서 특허 데이터를 로드합니다...")
                raw_patents = self.load_from_csv("patent_data.csv")
                
                if raw_patents:
                    state.raw_patents = raw_patents
                    print(f"총 {len(raw_patents)}개의 특허 데이터 로드 완료")
                    return state
            
            # CSV 파일이 없거나 비어있으면 API에서 수집
            print("KIPRIS API에서 특허 데이터를 수집합니다...")
            raw_patents = self.collect_from_api(
                cpc_number=Config.CPC_NUMBER,
                total_pages=Config.TOTAL_PAGES,
                num_of_rows=Config.NUM_OF_ROWS
            )
            
            if raw_patents:
                state.raw_patents = raw_patents
                print(f"총 {len(raw_patents)}개의 특허 데이터 수집 완료")
                
                # 수집한 데이터를 CSV로 저장
                df = pd.DataFrame(raw_patents)
                df.columns = ['ApplicationNumber', 'Registration Number', 'Invention Name', 'Abstract']
                df.to_csv("patent_data.csv", index=False, encoding="utf-8-sig")
                print("특허 데이터를 patent_data.csv에 저장했습니다.")
            else:
                print("수집된 특허 데이터가 없습니다.")

        except Exception as e:
            print(f"특허 데이터 수집 중 오류 발생: {e}")
            state.error_log.append(f"PatentCollectorAgent: {str(e)}")

        return state
