# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: PredictionMarketAgents
- **Team Members**: Nguyễn Quang Minh (2A202600195), Nguyễn Phương Nam (2A202600194)
- **Deployment Date**: 2026-04-06

---

## 1. Executive Summary

We built a **ReAct-based multi-agent prediction market system** where an LLM simulates trading behavior (YES/NO) to converge to a probability estimate for financial outcomes.

Instead of a single-shot chatbot, the agent iteratively:
- reasons (Thought),
- interacts with a market (Action),
- updates beliefs (Observation),
- and converges to a final probability.

- **Success Rate**: ~80% on test prompts
- **Key Outcome**: The ReAct agent produced **more structured, interpretable decisions** and handled multi-step reasoning significantly better than the chatbot baseline.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation

The agent follows a **Thought → Action → Observation → ... → Final Answer** loop:

1. User input is passed into the system prompt
2. LLM generates reasoning + action
3. Action is parsed and executed via tool
4. Observation is appended back to context
5. Loop continues until convergence or max_steps

This simulates a **prediction market price discovery process**.

---

### 2.2 Tool Definitions (Inventory)

| Tool Name   | Input Format | Use Case |
| :---------- | :----------- | :------- |
| `trade_yes` | `float`      | Increase probability (bullish signal) |
| `trade_no`  | `float`      | Decrease probability (bearish signal) |

These tools simulate a **market maker**, updating a probability value between 0 and 1.

---

### 2.3 LLM Providers Used

- **Primary**: LLaMA 3 (70B) via OpenRouter
- **Secondary (Fallback)**: LLaMA 3 (8B)

We replaced OpenAI GPT with OpenRouter to:
- reduce cost
- enable open-model experimentation
- test robustness on weaker instruction-following models

---

## 3. Telemetry & Performance Dashboard

Collected via `logger.py` and `metrics.py`.

- **Average Latency (P50)**: ~2500ms
- **Max Latency (P99)**: ~6000ms
- **Average Tokens per Task**: ~300–600 tokens
- **Total Cost of Test Suite**: ~$0.01–0.02 (estimated)

Observations:
- Multi-step reasoning increases latency significantly
- Token usage grows with loop depth

---

## 4. Root Cause Analysis (RCA) - Failure Traces

### Case Study: Invalid Tool Argument Format

- **Input**: "Will NVIDIA stock go up after strong earnings but high interest rates?"
- **Observation**: Model produced: Final Answer: trade_yes (input = 0.5)
- **Issue**: Parser expected `trade_yes(0.5)`

### Root Cause:
- LLaMA is less strict with formatting than GPT
- Prompt lacked strong constraints + examples

### Fix:
- Added regex normalization:
- converts `input = 0.5` → `0.5`
- Improved parsing robustness
- Extracted numeric values flexibly

---

### Case Study: Infinite Reasoning Loop

- **Observation**: Agent kept trading without stopping
- **Cause**:
- Model prefers continuing reasoning instead of terminating
- **Fix**:
- Early stop when `Final Answer` detected
- Enforced `max_steps = 5`

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs Prompt v2

- **Diff**:
- Added stricter format:
  ```
  Action: tool_name(number)
  Final Answer: number only
  ```
- **Result**:
- Reduced parsing errors by ~50%
- Improved convergence speed

---

### Experiment 2: Chatbot vs Agent

| Case        | Chatbot Result | Agent Result | Winner |
| :---------- | :------------- | :----------- | :----- |
| Simple Q    | Correct        | Correct      | Draw   |
| Multi-step  | Vague          | Structured   | **Agent** |
| Conflicting signals | Weak reasoning | Balanced probability | **Agent** |

---

## 6. Production Readiness Review

### Security
- Input validation needed for tool arguments
- Prevent prompt injection via tool descriptions

---

### Guardrails
- Max loop steps (currently 5)
- Early termination on Final Answer
- Fallback when parsing fails

---

### Scaling

To scale into real system:
- Replace mock tools with:
- real market engine (LMSR)
- real data APIs (Yahoo Finance, News API)
- Move to **LangGraph / multi-agent orchestration**
- Add:
- agent memory
- reputation weighting
- asynchronous execution

---

> [!NOTE]
> Submit this report by renaming it to `GROUP_REPORT_[TEAM_NAME].md` and placing it in this folder.
