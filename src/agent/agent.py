import re
from typing import List, Dict, Any
from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger


class ReActAgent:
    def __init__(self, llm: LLMProvider, tools: List[Dict[str, Any]], max_steps: int = 5):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.market_price = 0.5  # initial probability

    # -------------------------------
    # System Prompt
    # -------------------------------
    def get_system_prompt(self) -> str:
        tool_descriptions = "\n".join(
            [f"- {t['name']}: {t['description']}" for t in self.tools]
        )

        return f"""
You are an AI Investment Agent in a prediction market.

Available tools:
{tool_descriptions}

CRITICAL RULES:
- You MUST follow the format EXACTLY
- You MUST call at least one Action before Final Answer
- Action MUST be EXACTLY: trade_yes(number) or trade_no(number)
- DO NOT explain the action
- DO NOT write sentences inside Action

FORMAT:
Thought: reasoning
Action: trade_yes(0.5)
Observation: result
... (repeat if needed)
Final Answer: final probability with explanation
"""

    # -------------------------------
    # Main Loop
    # -------------------------------
    def run(self, user_input: str) -> str:
        logger.log_event("AGENT_START", {"input": user_input})

        current_prompt = user_input
        steps = 0

        while steps < self.max_steps:
            result = self.llm.generate(
                current_prompt,
                system_prompt=self.get_system_prompt()
            )

            output = result.get("content", "")

            if not output:
                return "Error: Empty response from model"

            print("\nDEBUG RAW OUTPUT:\n", output)

            logger.log_event("LLM_OUTPUT", {
                "step": steps,
                "output": output
            })

            # -------------------------------
            # 1. TERMINATION (ONLY AFTER ≥1 STEP)
            # -------------------------------
            if "Final Answer:" in output and steps > 0:
                answer = output.split("Final Answer:")[-1].strip()

                logger.log_event("AGENT_END", {
                    "steps": steps,
                    "answer": answer
                })

                return answer

            # -------------------------------
            # 2. PARSE ACTION
            # -------------------------------
            match = re.search(r"Action:\s*(\w+)\((.*?)\)", output)

            tool_name = None
            args = None

            if match:
                tool_name, args = match.group(1), match.group(2)
            else:
                # 🔥 fallback for messy LLaMA outputs
                if "trade_yes" in output:
                    tool_name = "trade_yes"
                    args = str(self.market_price)
                elif "trade_no" in output:
                    tool_name = "trade_no"
                    args = str(self.market_price)

            # -------------------------------
            # 3. EXECUTE TOOL
            # -------------------------------
            if tool_name:
                observation = self._execute_tool(tool_name, args)

                logger.log_event("TOOL_CALL", {
                    "tool": tool_name,
                    "args": args,
                    "observation": observation
                })

                current_prompt += f"\n{output}\nObservation: {observation}\n"
                steps += 1
                continue

            # -------------------------------
            # 4. FAILSAFE
            # -------------------------------
            logger.log_event("PARSER_ERROR", {"output": output})
            return "Error: Could not parse action."

        # -------------------------------
        # MAX STEP EXIT
        # -------------------------------
        logger.log_event("AGENT_END", {"steps": steps})
        return "Max steps reached without final answer."

    # -------------------------------
    # Tool Execution (Prediction Market)
    # -------------------------------
    def _execute_tool(self, tool_name: str, args: str) -> str:
        try:
            amount = float(args)
        except:
            amount = self.market_price

        # Simple price movement (mock AMM behavior)
        if tool_name == "trade_yes":
            self.market_price = min(1.0, self.market_price + 0.05)
        elif tool_name == "trade_no":
            self.market_price = max(0.0, self.market_price - 0.05)

        return f"{self.market_price:.2f}"