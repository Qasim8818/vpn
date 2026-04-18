# 🚀 LocalAgent Quick Start Guide

## ⚡ 5-Minute Setup

### 1. **Prerequisites Check**
```bash
# Verify Python 3.8+
python3 --version

# Check Docker
docker --version

# Check Ollama (install from https://ollama.com if needed)
ollama --version
```

### 2. **Clone/Enter Directory**
```bash
cd /home/killer123/Desktop/vpn
```

### 3. **Run Automated Setup** (Recommended)
```bash
chmod +x setup.sh
./setup.sh
```

This will:
- ✅ Install Python dependencies
- ✅ Pull Ollama models
- ✅ Start Qdrant vector database
- ✅ Create all necessary directories

### 4. **Verify Installation**
```bash
python3 validate.py
```

Expected output:
```
✓ Ollama is running
✓ Qdrant connected
✓ Embeddings working
✓ Memory operations OK
✓ Query generation OK
✓ RAG indexing OK
✓ Conversation history OK

✅ ALL TESTS PASSED
```

---

## 🎯 Using LocalAgent

### **Option A: Interactive Mode** (Recommended for Testing)
```bash
python3 agent_cli.py
```

**Commands**:
```
You: @query What is a VPN?
≈ Agent: [Detailed response with reasoning]

You: @fact I prefer async Python code
≈ Agent: ✓ Stored fact...

You: @codebase /home/killer123/Desktop/vpn
≈ Indexing...

You: @status
≈ Shows system health

You: @exit
```

### **Option B: Daemon Mode** (24/7 Background)
```bash
# Terminal 1: Start daemon
python3 agent_daemon.py

# Terminal 2: View logs
tail -f agent_daemon.log
```

### **Option C: Examples** (Learning)
```bash
python3 examples.py
```

Demonstrates:
- Basic queries
- Memory storage
- Preference learning
- Codebase RAG
- Multi-turn conversations

---

## 📚 File Structure

```
vpn/
├── local_agent.py           ← Main orchestrator
├── agent_cli.py             ← Interactive interface
├── agent_daemon.py          ← 24/7 background service
├── examples.py              ← Working examples
├── validate.py              ← System validation
├── requirements.txt         ← Python dependencies
├── config.json              ← Configuration
├── setup.sh                 ← Automated setup
│
├── README.md                ← Full documentation
├── ARCHITECTURE.md          ← Deep technical guide
│
├── ollama/
│   ├── ollama_client.py    ← LLM integration
│   ├── ollama_example.sh   ← Usage example
│   └── README.md
│
├── qdrant/
│   ├── local_memory.py     ← Persistent memory
│   ├── qdrant_example.py   ← Vector DB example
│   └── README.md
│
└── continue/
    ├── local_rag.py        ← Code indexing/search
    ├── config.json         ← Continue.dev config
    ├── continue_example.md ← RAG usage guide
    └── README.md
```

---

## 🧠 How It Works (30-Second Overview)

```
YOUR QUESTION
     ↓
EMBEDDING (Convert to vector)
     ↓
MEMORY SEARCH (Find relevant facts)
     ↓
RAG SEARCH (Find relevant code) [Optional]
     ↓
BUILD CONTEXT (Combine everything)
     ↓
CREATE PROMPT (Chain-of-thought)
     ↓
LLM REASONING (DeepSeek thinks step-by-step)
     ↓
STORE RESPONSE (Learn from interaction)
     ↓
YOUR ANSWER (With reasoning explained)
```

**Privacy**: All steps happen locally. No data leaves your machine.

---

## ✨ Key Features

| Feature | Details |
|---------|---------|
| **Reasoning** | Chain-of-Thought (thinks step-by-step) |
| **Memory** | Persistent across sessions (Qdrant) |
| **Learning** | Stores facts, preferences, code patterns |
| **Codebase** | Indexes and searches local code (RAG) |
| **Privacy** | 100% local, zero cloud calls |
| **Performance** | 2-30 seconds per query (no network latency) |
| **Availability** | 24/7 daemon mode available |

---

## 🔧 Common Tasks

### **Index Your Codebase**
```bash
python3 agent_cli.py

You: @codebase /path/to/your/project
≈ Indexed 156 chunks from 12 files
```

### **Store Important Facts**
```bash
You: @fact I use PostgreSQL for all databases
≈ ✓ Stored fact...
```

### **Set Preferences**
```bash
You: @pref language Python
≈ ✓ Stored preference...

You: @pref framework NestJS
≈ ✓ Stored preference...
```

### **Ask Questions (With Codebase Context)**
```bash
You: @query How is the LocalAgent architecture organized?
≈ Agent will search your indexed code and provide context-aware answer
```

### **See Conversation History**
```bash
You: @history
≈ Shows last 5 turns of conversation
```

---

## ⚡ Performance Tips

**For Faster Responses**:
```bash
# Use smaller model (8B instead of 14B)
ollama pull deepseek-r1:8b

# Edit ollama_client.py:
# self.model = "deepseek-r1:8b"
```

**For Better Reasoning**:
```bash
# Use larger model (32B)
ollama pull deepseek-r1:32b

# Requires 40GB+ RAM
```

**For GPU Acceleration**:
```bash
# Install NVIDIA CUDA support
# Then Ollama will auto-use GPU for 10x speedup
```

---

## 🐛 Troubleshooting

**"Ollama not responding"**
```bash
# Kill and restart
killall ollama
ollama serve
```

**"Qdrant connection refused"**
```bash
# Check Docker
docker ps | grep qdrant

# Restart if needed
docker run -d -p 6333:6333 qdrant/qdrant
```

**"Out of memory"**
```bash
# Check RAM usage
free -h

# Use smaller model or add more RAM
```

**"Python dependencies fail"**
```bash
# Try with Python venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📖 Next Steps

### **Level 1: Basics** (10 minutes)
- Run `python3 validate.py` to verify setup
- Run `python3 agent_cli.py` and try `@query "Hello"`
- Try `@fact "I like Python"` to test memory

### **Level 2: Intermediate** (30 minutes)
- Run `python3 examples.py` to see all features
- Index your own codebase with `@codebase /your/path`
- Ask queries about your code

### **Level 3: Advanced**
- Read `ARCHITECTURE.md` for deep technical knowledge
- Customize `config.json` for your preferences
- Run `python3 agent_daemon.py` for 24/7 operation
- Install as systemd service for auto-start

---

## 📞 Support

**Check Health**:
```bash
python3 -c "from local_agent import LocalAgent; LocalAgent().show_status()"
```

**View Logs**:
```bash
tail -f agent_daemon.log
```

**Run Tests**:
```bash
python3 validate.py
```

**See Examples**:
```bash
python3 examples.py
```

---

## 🎓 Learning Resources

- **README.md** ← Full feature documentation
- **ARCHITECTURE.md** ← Technical deep-dive
- **examples.py** ← Working code samples
- **ollama/README.md** ← LLM setup guide
- **qdrant/README.md** ← Memory system guide
- **continue/README.md** ← RAG/codebase guide

---

## 🎉 You're Ready!

You now have a powerful, private AI assistant running entirely on your machine.

**Start here**:
```bash
python3 agent_cli.py
```

**Type**: `@query "What can you help me with?"`

**Enjoy your LocalAgent!** 🤖✨

---

*Version 1.0.0 | April 2026 | Zero Cloud, All Local*
