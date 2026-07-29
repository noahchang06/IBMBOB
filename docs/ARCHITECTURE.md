# Architecture Specification: Creative Reasoning Platform

## 1. System Overview

The Creative Reasoning Platform is architected as a strict **Backend-Authoritative Application**. The FastAPI service hosts all domain models, knowledge graphs, constraint propagation algorithms, design system generators, and LLM orchestration logic. The React frontend is a purely visual presentation layer that utilizes D3.js solely for node coordinate computation in an isolated force simulation.

---

## 2. Core Engine Specifications

### A. Constraint Propagation Engine (`app/services/constraint_engine.py`)

The deterministic engine evaluates a 5-tuple vector of continuous constraints $C \in [0.0, 1.0]^5$:
$$C = \{ \text{visual\_tension}, \text{information\_density}, \text{accessibility}, \text{playfulness}, \text{material\_scarcity} \}$$

For each graph edge $E_i = (v_s, v_t, w_0, \tau)$, the modified weight $w'$ is calculated mathematically:

1. **Visual Tension ($C_{vt}$)**:
   - If $C_{vt} > 0.6$ and $\tau \in \{ \text{structural\_analogy}, \text{visual\_similarity} \}$: $w' \leftarrow w_0 \times (1 + (C_{vt} - 0.5))$
   - If $C_{vt} > 0.6$ and $\tau = \text{functional\_similarity}$: $w' \leftarrow w_0 \times (1 - 0.5(C_{vt} - 0.5))$

2. **Information Density ($C_{id}$)**:
   - Amplifies edges connected to high-density target nodes (Swiss Rail, Cockpit Instruments, Medical Imaging).
   - Attenuates edges connected to organic rest nodes (Japanese Garden, Butterfly Wing Patterns).

3. **Accessibility ($C_{acc}$)**:
   - Amplifies edges connected to universal safety models (Triage Systems, Wayfinding, Pharma Packaging).
   - Clamps weight bounds: $w' \in [0.1, 1.0]$.

4. **Node Importance Re-computation**:
   - Degree centrality recalculated post-propagation:
     $$\text{Importance}(v) = 0.2 + 0.8 \times \left( \frac{\sum_{e \in E(v)} w'_e}{\max_{u} \sum_{e \in E(u)} w'_e} \right)$$

---

### B. Design System Generator (`app/services/design_system_service.py`)

Generates fully formed design tokens from graph topology and constraint states:
- **Base Typography Size**: $S_{\text{base}} = 16 + \text{round}(6(C_{acc} - 0.5)) - \text{round}(4(C_{id} - 0.5))$
- **Scale Ratio**: $R_{\text{scale}} = \text{clamp}(1.25 + 0.3(C_{vt} - 0.5) - 0.2(C_{id} - 0.5), 1.15, 1.45)$
- **WCAG Compliance**:
  - $C_{acc} > 0.8 \implies \text{AAA}$ (Contrast ratio $\ge 7.0:1$)
  - $C_{acc} > 0.5 \implies \text{AA}$ (Contrast ratio $\ge 4.5:1$)

---

### C. IBM Granite Explanation Adapter (`app/services/explanation_service.py` & `app/services/mock_granite.py`)

The platform implements an abstract interface (`GraniteAdapter`) prepared for `watsonx` deployment:
- **Methods**:
  - `explain_edge_relationship(source, target, edge)`
  - `explain_design_decision(decision_name, constraints, design_system)`
  - `generate_reasoning_summary(graph, constraints, design_system)`
- **Boundary Guarantee**: Granite is invoked exclusively for qualitative analysis, alternative synthesis, and narrative explanation. It is prohibited from generating numerical weights or system metrics.

---

## 3. Database & Repository Abstraction (`app/db/`)

- Interface: `app/db/repository.py` defines abstract methods `save_project`, `load_project`, `save_snapshot`, `list_snapshots`.
- Concrete Implementation: `SQLiteRepository` in `app/db/sqlite_repository.py` using `aiosqlite`.
- Production Migration Path: Abstract design allows dropping in a PostgreSQL + `pgvector` repository implementation without modifying FastAPI routes or services.
