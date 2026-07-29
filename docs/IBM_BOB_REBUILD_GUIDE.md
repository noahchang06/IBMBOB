# IBM Bob Rebuild Guide: Creative Reasoning Platform

This document provides a comprehensive specification and prompt package so that **IBM Bob** (or any developer) can faithfully recreate the **Creative Reasoning Platform** from scratch without needing Antigravity.

---

## 1. System Specifications & Architectural Rules

### Core Architecture Rules
1. **Authoritative Backend**: All business logic (graph construction, constraint propagation, design token generation, degree centrality calculation, explanation orchestration) MUST reside in FastAPI (`backend/app/`).
2. **Presentation-Only Frontend**: React + Vite + Tailwind CSS (`frontend/src/`). D3.js is strictly isolated to computing node `(x, y)` coordinates via force simulation hooks (`useGraphLayout.ts`). D3 MUST NOT directly manipulate the DOM.
3. **Repository Abstraction**: Data persistence is handled behind an abstract `Repository` interface (`app/db/repository.py`). Development uses `SQLiteRepository` (`aiosqlite`); production targets `PostgreSQL` + `pgvector`.
4. **IBM Granite Provider**: LLM interactions are decoupled via `GraniteAdapter` (`app/services/mock_granite.py`). In production, swap in `watsonx.ai` SDK bindings (`watsonx_granite.py`).
5. **Strict Provenance Hierarchy**: Every data point in the UI MUST display its provenance label:
   - `[CURATED]`: Seed knowledge base data
   - `[SYSTEM]`: Deterministic math and engine outputs
   - `[RETRIEVED]`: Matched graph edges/evidence
   - `[AI]`: IBM Granite qualitative reasoning & narrative synthesis

---

## 2. Directory Structure Blueprint

```
creative-reasoning-platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py              # APIRouter (/api/health, /challenges, /graph/build, /apply-constraints, /explain, /export)
│   │   ├── data/
│   │   │   ├── knowledge_base.py      # Seed JSON loader & query interface
│   │   │   └── seed/
│   │   │       └── healthcare_dashboard.json # 12 Inspirations, 15 Edges
│   │   ├── db/
│   │   │   ├── repository.py          # Abstract Repository ABC
│   │   │   └── sqlite_repository.py   # aiosqlite implementation
│   │   ├── models/
│   │   │   ├── challenge.py           # PresetChallenge, ChallengeListResponse
│   │   │   ├── common.py              # DerivationLabel, LabeledValue, DomainType
│   │   │   ├── constraints.py         # ConstraintKey, ConstraintSet, ConstraintEffect
│   │   │   ├── design_system.py       # TypeScale, ColorToken, Palette, SpacingScale, ComponentStyle, DesignSystem
│   │   │   ├── explanation.py         # ReasoningStep, ExplanationChain, ExplanationRequest, ExplanationResponse
│   │   │   ├── export.py              # ExportRequest, ExportPackage
│   │   │   ├── graph.py              # EdgeType, GraphNode, GraphEdge, ReasoningGraph
│   │   │   └── inspiration.py        # TransferablePrinciple, Inspiration
│   │   ├── services/
│   │   │   ├── constraint_engine.py   # Matrix edge weight propagation engine
│   │   │   ├── design_system_service.py # Deterministic token generator
│   │   │   ├── explanation_service.py # Multi-tier explanation orchestrator
│   │   │   ├── graph_service.py       # Graph builder & degree centrality calculator
│   │   │   └── mock_granite.py        # IBM Granite mock & watsonx adapter template
│   │   ├── config.py                  # Pydantic Settings
│   │   └── main.py                    # FastAPI application & CORS configuration
│   ├── tests/
│   │   └── test_api.py                # 8 integration tests using TestClient
│   └── requirements.txt               # fastapi, uvicorn, pydantic, aiofiles, aiosqlite, httpx, python-dotenv, pytest
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── constraints/ConstraintPanel.tsx
    │   │   ├── design-system/DesignSystemPanel.tsx
    │   │   ├── discovery/DiscoveryView.tsx
    │   │   ├── explainable/ExplainablePanel.tsx
    │   │   ├── export/ExportPanel.tsx
    │   │   ├── graph/EdgeInspector.tsx
    │   │   ├── graph/ReasoningGraph.tsx
    │   │   ├── inspector/InspirationInspector.tsx
    │   │   ├── layout/AppShell.tsx, PanelContainer.tsx, Sidebar.tsx, TopBar.tsx
    │   │   └── shared/DerivationBadge.tsx, GlassCard.tsx
    │   ├── hooks/
    │   │   ├── useApi.ts              # REST API client hook
    │   │   └── useGraphLayout.ts      # D3 force simulation layout hook
    │   ├── store/
    │   │   └── appStore.ts            # Zustand global state store
    │   ├── types/
    │   │   └── index.ts               # Shared TypeScript interfaces & color maps
    │   ├── App.tsx
    │   ├── index.css                  # Tailwind CSS + dark mode styles
    │   └── main.tsx
    ├── package.json
    ├── tsconfig.json
    └── vite.config.ts
```

---

## 3. IBM Bob Prompt Sequence

When commissioning **IBM Bob** to build or extend this platform, execute the following prompt sequence:

### Prompt 1: Project Setup & Models
> "Initialize a FastAPI backend and React/Vite/Tailwind frontend for 'Creative Reasoning Platform'. In `backend/app/models/`, create Pydantic V2 models for `DerivationLabel` (CURATED, SYSTEM, RETRIEVED, AI), `Inspiration`, `ReasoningGraph`, `ConstraintSet`, `DesignSystem`, `ExplanationChain`, and `ExportPackage`. Ensure all models support provenance derivation tags."

### Prompt 2: Knowledge Base & Seed Data
> "Create `backend/app/data/seed/healthcare_dashboard.json` with 12 rich, peer-reviewed inspiration nodes (biology, architecture, industrial design, engineering, psychology) and 15 cross-domain edges. Create `knowledge_base.py` to auto-load seed data on startup."

### Prompt 3: Deterministic Constraint & Design System Engines
> "Implement `ConstraintEngine` in `backend/app/services/constraint_engine.py` to evaluate 5 constraints (visual_tension, information_density, accessibility, playfulness, material_scarcity) against edge types and target domains. Implement `DesignSystemService` to derive typography scales, palettes, spacing, and WCAG compliance deterministically."

### Prompt 4: Granite Adapter & FastAPI Routes
> "Implement `MockGraniteAdapter` and `ExplanationService` to structure multi-tier explanations. Create FastAPI endpoints at `/api/challenges`, `/api/graph/build`, `/api/graph/apply-constraints`, `/api/explain`, and `/api/export`. Ensure `/graph/build` and `/apply-constraints` return the updated graph, inspirations, and design system."

### Prompt 5: React Frontend & D3 Graph Layout
> "Build the frontend with React, Zustand, and Tailwind CSS. Implement `useGraphLayout.ts` using D3 force simulation to calculate node coordinates while letting React own SVG rendering. Build `DiscoveryView`, `ReasoningGraph`, `ConstraintPanel`, `DesignSystemPanel`, `ExplainablePanel`, and `ExportPanel`."

---

## 4. Rebuild Verification Checklist for IBM Bob

1. Backend pytest pass: `python -m pytest tests/` (8 tests green).
2. Frontend build pass: `npm run build` (0 TypeScript errors).
3. Graph interactive: D3 force layout nodes draggable; SVG zoom/pan functional.
4. Real-time constraint propagation: Sliders dynamically recalculate edge thickness and design system tokens.
5. Export verified: Generates valid `JSON` tokens and `Markdown` reasoning trace downloads.
