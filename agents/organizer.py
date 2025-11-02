import asyncio
from typing import Dict, Any, Tuple
from collections import defaultdict
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from state import PatentState
from config import Config


class PatentOrganizerAgent:
    """특허를 카테고리별로 정리하는 에이전트"""

    def __init__(self, llm: ChatOpenAI):
        self.name = "Patent Organizer"
        self.llm = llm
        # '기타' 카테고리를 추가하여 예상치 못한 응답에 대비합니다.
        self.categories = Config.PATENT_CATEGORIES + ["기타"]

        system_prompt = f"""당신은 특허 분류 전문가입니다.
        주어진 특허를 다음 카테고리 중 하나로 정확히 분류해주세요:
        {", ".join(Config.PATENT_CATEGORIES)}
        
        반드시 위 카테고리 중 하나만 선택하고, 카테고리 값만 반환하세요."""

        self.categorize_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "발명명: {title}\n요약: {summary}\n\n이 특허의 카테고리:"),
            ]
        )
        self.chain = self.categorize_prompt | self.llm

    async def categorize_single_patent(
        self, patent_item: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """단일 특허의 카테고리 판단"""
        # ① LLM 비동기 호출로 특허 분류
        response = await self.chain.ainvoke(
            {
                "title": patent_item.get("InventionName", ""),
                "summary": patent_item.get("ai_summary", patent_item.get("Abstract", "")),
            }
        )
        # ② LLM 응답에서 카테고리 추출
        category = response.content.strip()
        return category, patent_item

    async def organize_patents(self, state: PatentState) -> PatentState:
        """특허를 카테고리별로 정리"""
        print(f"\n[{self.name}] 특허 분류 시작...")

        summarized_patents = state.summarized_patents
        total_patents = len(summarized_patents)
        batch_size = Config.BATCH_SIZE
        # ③ 분류된 특허 저장을 위한 dict
        categorized = defaultdict(list)

        # ④ 배치 처리를 위한 루프
        for i in range(0, total_patents, batch_size):
            batch = summarized_patents[i : i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (total_patents + batch_size - 1) // batch_size

            print(f"  배치 {batch_num}/{total_batches} 분류 중...")

            # ⑤ 비동기 분류 작업 생성
            tasks = [self.categorize_single_patent(patent) for patent in batch]
            # ⑥ 모든 분류 작업 병렬 실행
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    print(f"    분류 작업 실패: {result}")
                    continue

                category, patent_item = result
                # ⑦ 반환된 카테고리 유효성 검사
                if category in Config.PATENT_CATEGORIES:
                    categorized[category].append(patent_item)
                else:
                    # ⑧ 정의되지 않은 카테고리는 '기타'로 처리
                    categorized["기타"].append(patent_item)

        print("\n  카테고리별 분포:")
        for category in self.categories:
            count = len(categorized.get(category, []))
            if count > 0:
                print(f"    {category}: {count}건")

        # ⑨ 상태 객체에 분류 결과 저장
        state.categorized_patents = dict(categorized)
        state.messages.append(
            AIMessage(content=f"특허를 {len(categorized)}개 카테고리로 분류했습니다.")
        )

        print(f"[{self.name}] 분류 완료\n")
        return state
