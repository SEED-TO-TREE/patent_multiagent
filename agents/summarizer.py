import asyncio
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from state import PatentState
from config import Config


class PatentSummarizerAgent:
    """특허를 요약하는 에이전트"""

    def __init__(self, llm: ChatOpenAI):
        self.name = "Patent Summarizer"
        self.llm = llm
        # ① 튜플 형식의 메시지로 간결하게 프롬프트 템플릿 구성
        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",  # ② 시스템 역할 메시지로 AI의 행동 지침 설정
                    """당신은 전문 특허 요약 전문가입니다. 
                    주어진 특허를 핵심만 간결하게 2-3문장으로 요약해주세요.
                    - 발명의 핵심 기술과 목적을 명확히 전달하세요
                    - 중요한 기술적 특징을 포함하세요
                    - 명확하고 이해하기 쉽게 작성하세요""",
                ),
                (
                    "human",  # ③ 사용자 메시지 템플릿에 변수 플레이스홀더 포함
                    "발명명: {title}\n요약: {content}\n\n위 특허를 2-3문장으로 요약해주세요:",
                ),
            ]
        )

    async def summarize_single_patent(self, patent_item: Dict[str, Any]) -> Dict[str, Any]:
        """단일 특허 요약 (오류 발생 시 원본 내용 반환)"""
        abstract = patent_item.get("Abstract", "")
        invention_name = patent_item.get("InventionName", "")
        
        try:
            # ④ 최소 콘텐츠 길이 검증으로 불필요한 API 호출 방지
            if not abstract or len(abstract) < 50:
                return {**patent_item, "ai_summary": abstract}

            # ⑤ LCEL(LangChain Expression Language) 체인 구성
            chain = self.prompt | self.llm
            summary_response = await chain.ainvoke(
                {
                    "title": invention_name,
                    "content": abstract[:1000],  # 특허 요약은 더 긴 텍스트 처리
                }
            )
            summary = summary_response.content.strip()
            # ⑥ 요약 결과 검증 및 폴백 처리
            return {**patent_item, "ai_summary": summary or abstract}

        except Exception as e:
            # ⑦ 간결한 오류 로깅과 원본 반환으로 서비스 연속성 보장
            print(
                f"  [{self.name}] 요약 오류 (발명명: {invention_name}): {str(e)[:50]}..."
            )
            return {**patent_item, "ai_summary": abstract}  # 오류 시 원본 사용

    async def summarize_patents(self, state: PatentState) -> PatentState:
        """모든 특허를 비동기로 요약"""
        print(f"\n[{self.name}] 특허 요약 시작...")

        batch_size = Config.BATCH_SIZE
        summarized_patents = []
        raw_patents = state.raw_patents
        total_patents = len(raw_patents)

        # ⑧ 배치 단위 순차 처리로 API 부하 분산
        for i in range(0, total_patents, batch_size):
            batch = raw_patents[i : i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_patents + batch_size - 1) // batch_size

            print(f"  배치 {batch_num}/{total_batches} 처리 중...")

            tasks = [self.summarize_single_patent(patent) for patent in batch]
            batch_results = await asyncio.gather(*tasks)
            summarized_patents.extend(batch_results)

        # ⑨ LangGraph 워크플로우 상태 업데이트
        state.summarized_patents = summarized_patents
        state.messages.append(
            AIMessage(content=f"{len(summarized_patents)}개의 특허 요약을 완료했습니다.")
        )

        print(f"[{self.name}] 요약 완료\n")
        return state
