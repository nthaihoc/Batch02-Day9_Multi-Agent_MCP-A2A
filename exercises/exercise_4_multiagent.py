"""Bài Tập 4: Thêm Privacy Agent vào Multi-Agent System

Hoàn thành các TODO để thêm privacy agent và conditional routing.
"""

import asyncio
import os
import sys
from typing import Annotated, TypedDict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from common.llm import get_llm


def _last_wins(left: str | None, right: str | None) -> str:
    """Reducer: giá trị mới ghi đè giá trị cũ."""
    return right if right is not None else (left or "")


class State(TypedDict):
    question: str
    law_analysis: Annotated[str, _last_wins]
    tax_analysis: Annotated[str, _last_wins]
    compliance_analysis: Annotated[str, _last_wins]
    privacy_analysis: Annotated[str, _last_wins]  # Đã kích hoạt field cho Privacy
    final_response: str


def law_agent(state: State) -> dict:
    """Agent phân tích pháp lý tổng quát."""
    llm = get_llm()
    prompt = f"""Bạn là chuyên gia pháp lý. Phân tích câu hỏi sau:

{state['question']}

Tập trung vào: hợp đồng, trách nhiệm dân sự, quyền và nghĩa vụ pháp lý."""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"law_analysis": response.content}


def check_routing(state: State) -> list[Send]:
    """Quyết định gọi agents chuyên sâu nào dựa trên nội dung câu hỏi."""
    question_lower = state["question"].lower()
    tasks = []
    
    if any(kw in question_lower for kw in ["tax", "irs", "thuế"]):
        tasks.append(Send("tax_agent", state))
    
    if any(kw in question_lower for kw in ["compliance", "sec", "regulation", "tuân thủ"]):
        tasks.append(Send("compliance_agent", state))
    
    # Đã hoàn thành TODO: Thêm logic routing cho privacy_agent
    if any(kw in question_lower for kw in ["data", "privacy", "gdpr", "dữ liệu", "bảo mật", "rò rỉ"]):
        tasks.append(Send("privacy_agent", state))
    
    # Nếu câu hỏi có liên quan đến lĩnh vực chuyên sâu, điều phối cho các agent tương ứng.
    # Nếu không, bỏ qua các agent chuyên sâu và đi thẳng đến hàm tổng hợp (aggregate_results).
    return tasks if tasks else [Send("aggregate_results", state)]


def tax_agent(state: State) -> dict:
    """Agent chuyên về thuế."""
    llm = get_llm()
    prompt = f"""Bạn là chuyên gia thuế. Phân tích khía cạnh thuế trong câu hỏi:

Câu hỏi: {state['question']}
Phân tích pháp lý cơ sở: {state.get('law_analysis', 'N/A')}

Tập trung: IRS, tax evasion, penalties, FBAR, FATCA, luật quản lý thuế."""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"tax_analysis": response.content}


def compliance_agent(state: State) -> dict:
    """Agent chuyên về compliance."""
    llm = get_llm()
    prompt = f"""Bạn là chuyên gia tuân thủ. Phân tích khía cạnh tuân thủ:

Câu hỏi: {state['question']}
Phân tích pháp lý cơ sở: {state.get('law_analysis', 'N/A')}

Tập trung: SEC, SOX, FCPA, AML, regulatory violations, quy định ban ngành."""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"compliance_analysis": response.content}


# Đã hoàn thành TODO: Implement privacy_agent
def privacy_agent(state: State) -> dict:
    """Agent chuyên về bảo vệ dữ liệu cá nhân và quyền riêng tư."""
    llm = get_llm()
    prompt = f"""Bạn là chuyên gia bảo vệ dữ liệu và quyền riêng tư. Phân tích khía cạnh bảo mật:

Câu hỏi: {state['question']}
Phân tích pháp lý cơ sở: {state.get('law_analysis', 'N/A')}

Tập trung: GDPR, data protection, privacy rights, data breach, rủi ro đánh cắp dữ liệu, Nghị định 13/2023/NĐ-CP (nếu áp dụng tại VN)."""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"privacy_analysis": response.content}


def aggregate_results(state: State) -> dict:
    """Tổng hợp kết quả từ tất cả agents."""
    llm = get_llm()
    
    sections = []
    if state.get("law_analysis"):
        sections.append(f"📋 PHÂN TÍCH PHÁP LÝ TỔNG QUÁT:\n{state['law_analysis']}")
    if state.get("tax_analysis"):
        sections.append(f"💰 PHÂN TÍCH THUẾ:\n{state['tax_analysis']}")
    if state.get("compliance_analysis"):
        sections.append(f"✅ PHÂN TÍCH TUÂN THỦ:\n{state['compliance_analysis']}")
        
    # Đã hoàn thành TODO: Thêm privacy_analysis vào sections
    if state.get("privacy_analysis"):
        sections.append(f"🔒 PHÂN TÍCH BẢO MẬT & QUYỀN RIÊNG TƯ:\n{state['privacy_analysis']}")
    
    combined = "\n\n".join(sections)
    
    prompt = f"""Bạn là luật sư cấp cao (Senior Partner). Hãy tổng hợp các bản phân tích từ đội ngũ chuyên gia của bạn thành một báo cáo cuối cùng để gửi khách hàng:

{combined}

Câu hỏi gốc của khách hàng: {state['question']}

Yêu cầu:
- Tạo một báo cáo ngắn gọn, sử dụng cấu trúc rõ ràng (Markdown, tiêu đề lớn, bullet points).
- Có một đoạn "Kết luận và Khuyến nghị" chung ở cuối báo cáo."""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return {"final_response": response.content}


def build_graph() -> StateGraph:
    """Xây dựng multi-agent graph."""
    graph = StateGraph(State)
    
    # 1. Thêm các nodes (Các Agents & Hàm xử lý)
    graph.add_node("law_agent", law_agent)
    graph.add_node("check_routing", check_routing)
    graph.add_node("tax_agent", tax_agent)
    graph.add_node("compliance_agent", compliance_agent)
    
    # Đã hoàn thành TODO: Thêm privacy_agent node
    graph.add_node("privacy_agent", privacy_agent)
    graph.add_node("aggregate_results", aggregate_results)
    
    # 2. Định nghĩa đường đi (Edges)
    graph.add_edge(START, "law_agent")           # Bắt đầu -> Phân tích chung
    graph.add_edge("law_agent", "check_routing") # Phân tích chung xong -> Bộ định tuyến
    
    # Định tuyến động dựa trên hàm check_routing (gọi song song các agent cần thiết)
    graph.add_conditional_edges("check_routing", lambda x: x)
    
    # Sau khi các agent chuyên sâu làm việc xong -> Đưa về hàm tổng hợp
    graph.add_edge("tax_agent", "aggregate_results")
    graph.add_edge("compliance_agent", "aggregate_results")
    
    # Đã hoàn thành TODO: Thêm edge từ privacy_agent đến aggregate_results
    graph.add_edge("privacy_agent", "aggregate_results")
    
    graph.add_edge("aggregate_results", END)     # Tổng hợp xong -> Kết thúc quy trình
    
    return graph.compile()


async def main():
    load_dotenv()
    
    # Test với câu hỏi gọi ra Privacy Agent và Tax Agent
    question = "Nếu công ty bị rò rỉ dữ liệu khách hàng, hậu quả pháp lý và thuế là gì?"
    
    print("=" * 70)
    print("MULTI-AGENT SYSTEM với Privacy Agent")
    print("=" * 70)
    print(f"\nCâu hỏi: {question}\n")
    print("Đang xử lý qua các agents...\n")
    
    graph = build_graph()
    
    # Khởi tạo state rỗng ban đầu
    initial_state = {
        "question": question,
        "law_analysis": "",
        "tax_analysis": "",
        "compliance_analysis": "",
        "privacy_analysis": "",
        "final_response": "",
    }
    
    result = await graph.ainvoke(initial_state)
    
    print("\n" + "=" * 70)
    print("KẾT QUẢ CUỐI CÙNG")
    print("=" * 70)
    print(result["final_response"])
    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())