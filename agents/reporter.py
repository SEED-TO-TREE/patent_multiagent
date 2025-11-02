from datetime import datetime
from langchain_core.messages import AIMessage

from state import PatentState
from config import Config


class ReportGeneratorAgent:
    """최종 보고서를 생성하는 에이전트"""

    def __init__(self):
        self.name = "Report Generator"

    async def generate_report(self, state: PatentState) -> PatentState:
        """최종 보고서 생성"""
        print(f"\n[{self.name}] 보고서 생성 시작...")
        report_parts = []

        current_time = datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")
        # ① 모든 카테고리의 특허 개수를 합산하여 처리된 총 특허 수 계산
        total_processed = sum(len(v) for v in state.categorized_patents.values())
        header = f"""# KIPRIS 특허 AI 요약 리포트

## 기본 정보
- **수집 시간**: {current_time}
- **데이터 소스**: KIPRIS API / patent_data.csv
- **수집 특허**: {len(state.raw_patents)}건
- **처리 완료**: {total_processed}건"""
        report_parts.append(header)

        # 통계 섹션
        # ② 딕셔너리 컴프리헨션으로 각 카테고리별 특허 개수 집계
        category_stats = {
            cat: len(patents) for cat, patents in state.categorized_patents.items()
        }
        total_patents = sum(category_stats.values())
        if total_patents > 0:
            # ③ 마크다운 테이블 헤더 생성 (파이프 문자로 열 구분)
            table_header = (
                "| 카테고리 | 특허 수 | 비율 |\n|---------|--------|------|\n"
            )
            # ④ 특허 수가 많은 순으로 정렬하여 테이블 행 생성
            table_rows = [
                f"| {cat} | {count}건 | {(count / total_patents) * 100:.1f}% |"
                for cat, count in sorted(
                    category_stats.items(), key=lambda x: x[1], reverse=True
                )
                if count > 0
            ]
            stats_table = table_header + "\n".join(table_rows)
            stats_section = f"## 카테고리별 특허 분포\n\n{stats_table}"
            report_parts.append(stats_section)

        # 카테고리별 특허 섹션 생성
        patent_sections = []
        for category in Config.PATENT_CATEGORIES:
            # ⑤ Walrus 연산자(:=)로 할당과 조건 검사를 동시에 수행
            if patent_list := state.categorized_patents.get(category):
                section_header = f"### {category} ({len(patent_list)}건)\n"
                # ⑥ 카테고리별 표시 개수 제한 (Config.PATENT_PER_CATEGORY = 30)
                display_count = min(len(patent_list), Config.PATENT_PER_CATEGORY)

                # ⑦ enumerate로 순번 매기며 특허 항목 문자열 생성
                patent_items_str = "\n".join(
                    f"""#### {i}. {patent.get("InventionName", "N/A")}
- **출원번호**: {patent.get("ApplicationNumber", "N/A")}
- **등록번호**: {patent.get("RegistrationNumber", "N/A")}
- **요약**: {patent.get("ai_summary", patent.get("Abstract", ""))}"""
                    for i, patent in enumerate(patent_list[:display_count], 1)
                )

                patent_sections.append(f"{section_header}\n{patent_items_str}")

        if patent_sections:
            # ⑧ 각 카테고리 섹션을 구분선(---)으로 연결
            report_parts.append(
                "## 카테고리별 주요 특허\n\n" + "\n\n---\n\n".join(patent_sections)
            )

        if state.error_log:
            errors = "\n".join([f"- {error}" for error in state.error_log])
            report_parts.append(f"## 처리 중 발생한 오류\n\n{errors}")

        # 푸터 생성
        footer = """## 참고사항
- 이 보고서는 AI(LangGraph + LangChain)를 활용하여 자동으로 생성되었습니다.
- 특허 요약은 OpenAI GPT 모델을 사용하여 작성되었습니다.
- 카테고리 분류는 AI가 발명명과 요약을 분석하여 자동으로 수행했습니다.
- 상세한 내용은 KIPRIS 웹사이트에서 출원번호로 검색하시기 바랍니다."""
        report_parts.append(footer)

        # 최종 보고서 조합
        state.final_report = "\n\n---\n\n".join(report_parts)
        state.messages.append(AIMessage(content="최종 보고서가 생성되었습니다."))

        print(f"[{self.name}] 보고서 생성 완료")
        return state
