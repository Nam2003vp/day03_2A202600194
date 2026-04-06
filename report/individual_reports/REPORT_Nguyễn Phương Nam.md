# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: [Nguyễn Phương Nam]
- **Student ID**: [2A202600194]
- **Date**: [2026-04-06]

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: `src/agents/agent.py (ReAct Investment Agent)`
Integrated trading tools: trade_yes, trade_no (mock AMM simulation)

- **Code Highlights**: 
[def get_system_prompt(self) -> str:]
Thiết kế một system prompt chuyên biệt cho prediction market, trong đó:

- Ép agent phải gọi ít nhất một Action
Giới hạn Action hợp lệ chỉ còn:
 trade_yes(number)
 trade_no(number)
- Loại bỏ hoàn toàn language dư thừa trong Action để tránh parsing lỗi

[match = re.search(r"Action:\s*(\w+)\((.*?)\)", output)]
- Bổ sung fallback logic 

[if "trade_yes" in output: tool_name = "trade_yes"]
- biện pháp defensive programming nhằm tăng độ ổn định của agent khi model không tuân thủ prompt tuyệt đối

[if "Final Answer:" in output and steps > 0:]
- Agent chỉ được phép kết thúc sau khi đã trade ít nhất 1 lần

[def _execute_tool(self, tool_name: str, args: str) -> str:]
tool trade_yes/trade_no mô phỏng AMM đơn giản:
- Giá tăng khi buy YES
- Giá giảm khi buy NO
- Market price luôn nằm trong [0,1]

- **Documentation**: 
Agent hoạt động theo chu trình:
1. LLM sinh Thought dựa trên market state
2. LLM quyết định Action(trade)
3. Tool thực hiện trade → cập nhật market_price
4. Giá mới được đưa lại dưới dạng Observation
5. LLM điều chỉnh belief và quyết định bước tiếp theo
---

## II. Debugging Case Study (10 Points)

- **Problem Description**: Agent sinh ra Action không đúng cú pháp yêu cầu, dẫn đến lỗi parsing và dừng agent sớm.

- **Log Source**: [{
  "event": "PARSER_ERROR",
  "output": "Thought: ... Action: trade yes 0.5"
}]
Log cho thấy agent không thể trích xuất tool_name và args bằng regex chuẩn, dẫn đến việc kích hoạt fail-safe và kết thúc sớm vòng lặp.

- **Diagnosis**: 
Nguyên nhân chính đến từ model compliance với system prompt:
LLM không tuân thủ chặt cú pháp hàm, đặc biệt khi:
Model over-explain trong Action
Model sử dụng dấu cách thay vì dấu gạch dưới
Đây không phải lỗi logic ReAct loop hay tool execution
Prompt ban đầu chưa đủ “cứng” để ràng buộc hành vi của model trong domain tài chính

- **Solution**: 
Trong get_system_prompt(), bổ sung các ràng buộc chặt chẽ hơn:
- Action MUST be EXACTLY: trade_yes(number) or trade_no(number)
- DO NOT explain the action
- DO NOT write sentences inside Action

- Để tăng độ robust của agent, bổ sung logic fallback:
if "trade_yes" in output:
    tool_name = "trade_yes"
    args = str(self.market_price)
elif "trade_no" in output:
    tool_name = "trade_no"
    args = str(self.market_price)

Kết quả sau khi sửa:

Agent không còn rơi vào lỗi parser thường xuyên
ReAct loop vận hành ổn định ngay cả với output không hoàn hảo
Logging tiếp tục ghi nhận đầy đủ hành vi agent để debug

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1.  **Reasoning**: 
Khối Thought cho phép:
- Quan sát belief update của agent
- Hiểu tại sao agent trade YES hoặc NO
- Debug được decision logic theo từng step
ReAct agent xây dựng xác suất thông qua hành động
2.  **Reliability**: 
Agent hoạt động kém hơn chatbot trong các trường hợp:
- Market câu hỏi đơn giản
- Không cần interaction (one-shot prediction)
- Model yếu → overthinking, trade không cần thiết
Điều này cho thấy agent không luôn tối ưu cho task ngắn.
3.  **Observation**: 
Đóng vai trò:
- Feedback môi trường   
- Giống Bayesian update (belief ← evidence)
- Nếu observation sai → entire reasoning chain sai
Điều này làm agent giống reinforcement-style loop hơn chatbot NLP.

---

## IV. Future Improvements (5 Points)

- **Scalability**: 
Tách market simulation thành service độc lập
Cho phép multiple agents trade song song
- **Safety**: 
Thêm Supervisor Agent
Check extreme trades
Detect oscillation YES↔NO
- **Performance**: 
Learnable market impact model
Replace hardcoded ±0.05 bằng learned dynamics
Memory buffer cho historical trades

---

