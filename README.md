# Emotion-Aware Chat System  
### An OS-Style Architecture for Emotion-Aware AI Interaction

This project is an *emotion-aware AI chat system* designed with an *operating-system-inspired architecture*.

Instead of treating a large language model (LLM) as a black-box chatbot, this system treats AI as a *managed computational resource*, emphasizing:
- task scheduling
- priority-based resource allocation
- asynchronous execution
- emotion-aware decision pipelines

The project explores how *Operating Systems concepts* can be applied to modern *AI-powered interactive systems*.

---

## ✨ Key Features

### Emotion-Aware Processing
- Incoming user messages are analyzed for emotional state (e.g., sad, angry, anxious, neutral).
- Emotion severity influences both:
  - task scheduling priority
  - AI response strategy

### OS-Style Architecture
- Producer–Consumer model using an in-memory *priority queue*
- Background *worker* consumes tasks asynchronously
- Emotionally critical messages are processed first

### Streaming AI Responses
- WebSocket-based real-time streaming
- Partial AI-generated tokens are sent incrementally
- Provides ChatGPT-like real-time interaction experience

### LLM as a Managed Resource
- The system decides when and how to invoke the LLM
- Emotion analysis and policy decisions occur *before* LLM execution
- Timeout and fallback mechanisms prevent blocking and resource starvation

---

## 🧠 System Architecture Overview

This architecture mirrors classic OS components:

| OS Concept | This System |
|-----------|-------------|
| Process | User request |
| Ready Queue | Priority task queue |
| Scheduler | Worker logic |
| CPU | LLM execution |
| I/O | WebSocket streaming |

---

## 🛠 Tech Stack

### Backend
- Python 3.11+
- FastAPI
- WebSocket (real-time streaming)
- asyncio

### AI & NLP
- Rule-based emotion analyzer (extensible to ML/DL)
- OpenAI API (streaming completions)

### System Design Concepts
- Producer–Consumer pattern
- Priority scheduling
- Asynchronous workers
- Fault isolation (timeouts, fallbacks)