"""
데이터 모델 정의하기 - 시스템에서 사용할 데이터 구조 정의
"""
from typing import Annotated, Any
from pydantic import BaseModel, ConfigDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class PatentState(BaseModel):
    """특허 처리 상태를 관리하는 BaseModel"""

    model_config = ConfigDict(arbitrary_types_allowed=True) # pydantic이 모르는 타입을 허용
    # 대화의 히스토리 저장을 위한 필드
    messages: Annotated[list[BaseMessage], add_messages] = []
    # KIPRIS API가 수집한 특허 데이터 저장
    raw_patents: list[dict[str, Any]] = []
    # AI가 요약한 특허 데이터 저장
    summarized_patents: list[dict[str, Any]] = []
    # 카테고리별로 분류된 특허 데이터 저장
    categorized_patents: dict[str, list[dict[str, Any]]] = {}
    # 리포트 문자열로 저장
    final_report: str = ""
    # 에러 로그 저장
    error_log: list[str] = []
