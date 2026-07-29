# Creative Reasoning Platform
> **Discover. Reason. Design. Understand. Export.**

An AI-powered creative reasoning platform designed for cross-domain innovation, constraint manipulation, explainable design system evolution, and traceably evidence-backed creative decision-making. Built for the **IBM AI Builders Challenge**.

---

## 🌟 Executive Vision: AI as a Creative Reasoning Partner

Current generative AI tools focus almost exclusively on **content generation** — spitting out unstructured text, images, or code without explaining *why* design choices were made. 

The **Creative Reasoning Platform** flips this paradigm. It acts as an **explainable creative reasoning partner**:
- It uncovers unexpected cross-domain analogies (e.g., how Emergency Department Triage systems and Japanese Garden spatial flow inform clinical monitoring dashboard UX).
- It provides deterministic, evidence-backed constraint propagation where visual, structural, and behavioral principles dictate UI design tokens in real time.
- Every node, relationship, constraint, and design token carries explicit **provenance metadata** — eliminating AI hallucination and black-box decision-making.

---

## 🏛️ System Architecture & Provenance Model

```
                    ┌─────────────────────────────────────────┐
                    │            React + Vite UI              │
                    │   (D3 Force Layout, Zustand Store)      │
                    └────────────────────┬────────────────────┘
                                         │ REST API
                    ┌────────────────────▼────────────────────┐
                    │      FastAPI Authoritative Engine       │
                    │ ┌─────────────────────────────────────┐ │
                    │ │ Graph Engine (Seed & Centrality)    │ │
                    │ │ Deterministic Constraint Engine     │ │
                    │ │ Design System Token Generator       │ │
                    │ │ Multi-Layer Explanation Pipeline    │ │
                    │ └──────────────────┬──────────────────┘ │
                    └────────────────────┼────────────────────┘
                                         │ Abstract Repository Interface
                    ┌────────────────────▼────────────────────┐
                    │    SQLite Store (Dev) -> pgvector (Prod) │
                    └─────────────────────────────────────────┘
```

### Derivation & Provenance Taxonomy

To ensure 100% feasibility and eliminate fake or magical claims:
- `[CURATED]`: Peer-reviewed historical facts, domain principles, and documented case studies.
- `[SYSTEM]`: Deterministic algorithmic outputs (degree centrality, constraint propagation, contrast ratios, WCAG compliance).
- `[RETRIEVED]`: Matched knowledge graph relationships and evidence snippets.
- `[AI]`: Generative reasoning interpretations, contextual trade-off analysis, and principle extractions powered by **IBM Granite**.

---

## 🚀 Quickstart Guide

### Prerequisites
- Python 3.10+
- Node.js 18+

### 1. Backend Setup (FastAPI)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest

# Run automated backend test suite
python -m pytest tests/

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup (React + Vite + Tailwind)
```bash
cd frontend
npm install
npm run build
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## 💼 Real-World Impact across Domains

1. **Healthcare & MedTech**: Design safety-critical clinical monitoring interfaces with glanceable triage hierarchies, low cognitive load, and zero visual ambiguity under fatigue.
2. **Product & Industrial Design**: Translate physical material constraints (scarcity, durability, spatial rhythm) directly into digital UI behavior and token systems.
3. **UX & Design Systems**: Transform subjective design discussions into traceable, evidence-backed decisions aligned with universal accessibility standards.
4. **Architecture & Spatial Design**: Apply wayfinding, progressive disclosure, and spatial composition rules to complex software interfaces.
5. **Government & Public Policy**: Build transparent, accessible citizen-facing portals grounded in Swiss clarity and cognitive psychology.
6. **Education & EdTech**: Engage students with explainable cross-domain reasoning graphs bridging biology, physics, history, and art.
7. **Creative Agencies & Brand Strategy**: Provide clients with rationale reports explaining the exact mathematical and cognitive logic behind custom design systems.

---

## 🧪 Testing & Verification

Run the full automated verification suite:
```bash
cd backend && source .venv/bin/activate && python -m pytest tests/
```

All 8 integration tests verify:
- Knowledge base initialization & seed parsing
- Graph centrality & node importance computation
- Dynamic constraint propagation & edge weight modulation
- Contrast ratio & WCAG AAA compliance enforcement
- Multi-tier explanation payload formatting
- Full package JSON/Markdown export pipeline

---

## 📄 License & Attribution

Developed for the **IBM AI Builders Challenge**. Built with FastAPI, React, D3.js, TailwindCSS, and IBM Granite adapter architectures.
