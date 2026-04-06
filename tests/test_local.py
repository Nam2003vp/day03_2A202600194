import os
import sys
from dotenv import load_dotenv

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.agent import ReActAgent
from src.core.openai_provider import OpenAIProvider
# (Optional fallback)
# from src.core.local_provider import LocalProvider


# -------- TOOLS --------
def trade_yes(args: str) -> str:
    try:
        return str(min(float(args) + 0.05, 1.0))
    except:
        return "error"


def trade_no(args: str) -> str:
    try:
        return str(max(float(args) - 0.05, 0.0))
    except:
        return "error"


tools = [
    {
        "name": "trade_yes",
        "description": "Increase probability (input = current price)",
        "func": trade_yes,
    },
    {
        "name": "trade_no",
        "description": "Decrease probability (input = current price)",
        "func": trade_no,
    },
]


def test_prediction_market_agent():
    load_dotenv()

    print("\n--- Testing ReAct Prediction Market Agent (LLaMA via OpenRouter) ---")

    try:
        # ---- Use LLaMA via OpenRouter ----
        provider = OpenAIProvider()

        # ---- (Optional) fallback to local ----
        # provider = LocalProvider(model_path="./models/Phi-3-mini-4k-instruct-q4.gguf")

        agent = ReActAgent(llm=provider, tools=tools)

        prompt = "Will NVIDIA stock go up after strong earnings but high interest rates?"

        print(f"\nUser: {prompt}")
        print("Agent:\n")

        result = agent.run(prompt)

        print("\nFINAL RESULT:\n", result)

        print("\n✅ Agent test completed!")

    except Exception as e:
        print(f"\n❌ Error during execution: {e}")


if __name__ == "__main__":
    test_prediction_market_agent()