"""Bài Tập 2: Thêm Tools và Knowledge Base

Hoàn thành các TODO để thêm tool và knowledge base entry mới.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from common.llm import get_llm

# Knowledge base
LEGAL_KNOWLEDGE = [
    {
        "id": "ucc_breach",
        "keywords": ["breach", "contract", "remedies", "damages", "ucc"],
        "text": (
            "Under the Uniform Commercial Code (UCC) Article 2, remedies for breach of contract "
            "include: (1) expectation damages; (2) consequential damages; (3) specific performance; "
            "(4) cover damages. Statute of limitations is typically 4 years (UCC § 2-725)."
        ),
    },
    # Đã hoàn thành TODO: Thêm entry về luật lao động Việt Nam
    {
        "id": "vn_labor_law",
        "keywords": ["lao động", "sa thải", "hợp đồng lao động", "nghỉ việc", "bồi thường"],
        "text": (
            "Theo Bộ luật Lao động Việt Nam, người sử dụng lao động khi đơn phương chấm dứt hợp đồng "
            "trái pháp luật phải nhận người lao động trở lại làm việc, trả tiền lương, BHXH, BHYT, BHTN "
            "trong những ngày không được làm việc và phải bồi thường ít nhất 02 tháng tiền lương."
        ),
    }
]

@tool
def search_legal_knowledge(query: str) -> str:
    """Tìm kiếm trong knowledge base pháp lý dựa trên từ khóa."""
    query_lower = query.lower()
    for entry in LEGAL_KNOWLEDGE:
        if any(kw in query_lower for kw in entry["keywords"]):
            return f"[{entry['id']}] {entry['text']}"
    return "Không tìm thấy thông tin liên quan."

# Đã hoàn thành TODO: Tạo tool check_statute_of_limitations
@tool
def check_statute_of_limitations(case_type: str) -> str:
    """Kiểm tra thời hiệu khởi kiện dựa trên loại vụ án (case_type)."""
    case_type_lower = case_type.lower()
    if "hợp đồng" in case_type_lower or "contract" in case_type_lower:
        return "Thời hiệu khởi kiện đối với tranh chấp hợp đồng thông thường là 03 năm kể từ ngày người có quyền yêu cầu biết quyền lợi bị xâm phạm."
    elif "thừa kế" in case_type_lower:
        return "Thời hiệu khởi kiện về quyền thừa kế là 10 năm đối với động sản và 30 năm đối với bất động sản."
    elif "lao động" in case_type_lower:
        return "Thời hiệu khởi kiện tranh chấp lao động cá nhân là 01 năm kể từ ngày phát hiện ra hành vi vi phạm."
    else:
        return f"Hiện chưa có thông tin thời hiệu khởi kiện cụ thể cho loại án: '{case_type}' trong hệ thống."

async def main():
    load_dotenv()
    llm = get_llm()
    
    # Đã hoàn thành TODO: Thêm tool mới vào danh sách
    tools = [search_legal_knowledge, check_statute_of_limitations]
    llm_with_tools = llm.bind_tools(tools)
    
    # Tối ưu hóa: Tạo một dictionary ánh xạ tên tool với function thực tế của nó
    tool_map = {t.name: t for t in tools}
    
    question = "Thời hiệu khởi kiện vụ vi phạm hợp đồng là bao lâu?"
    
    messages = [
        SystemMessage(content="Bạn là chuyên gia pháp lý. Sử dụng tools để tra cứu thông tin và trả lời người dùng."),
        HumanMessage(content=question),
    ]
    
    print(f"Câu hỏi: {question}\n")
    
    # Cuộc gọi LLM lần 1 - Quyết định xem có cần dùng tool nào không
    response = await llm_with_tools.ainvoke(messages)
    messages.append(response)
    
    # Thực thi tool nếu LLM yêu cầu
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            print(f"🔧 Gọi tool: {tool_name}")
            
            # Đã hoàn thành TODO: Xử lý gọi tool linh hoạt thay vì dùng if/else phần cứng
            if tool_name in tool_map:
                selected_tool = tool_map[tool_name]
                tool_result = selected_tool.invoke(tool_call["args"])
                
                if tool_result:
                    messages.append(ToolMessage(content=tool_result, tool_call_id=tool_call["id"]))
            else:
                print(f"⚠️ Không tìm thấy tool: {tool_name}")
        
        # Cuộc gọi LLM lần 2 - Tổng hợp câu trả lời cuối cùng từ kết quả của tool
        final_response = await llm_with_tools.ainvoke(messages)
        print(f"\n✅ Kết quả:\n{final_response.content}")
    else:
        print(f"\n✅ Kết quả:\n{response.content}")

if __name__ == "__main__":
    asyncio.run(main())