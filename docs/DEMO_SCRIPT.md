# Competition Demo Script (3-Minute Judge Presentation)

**Product**: Creative Reasoning Platform  
**Subtitle**: Discover. Reason. Design. Understand. Export.  
**Target Audience**: IBM AI Builders Challenge Judges  

---

## 🕒 Timestamped Demo Protocol

### 0:00 - 0:30 | The Hook: Unlocking Creative Reasoning (First 30 Seconds)
- **Visual**: Discovery View with dark-mode aesthetic and 3 preset challenge cards.
- **Narrative**: 
  > "Most AI design tools generate random UI mockups or raw text. They give you content, but they don't explain *why* design decisions were made. 
  > 
  > Welcome to the **Creative Reasoning Platform**. Here, AI acts as an explainable creative reasoning partner — connecting unexpected cross-domain insights to derive evidence-backed design systems."

---

### 0:30 - 1:15 | Step 1: Discover & Map (Graph Visualizer)
- **Action**: Click **Healthcare Dashboard** (*"Designing clarity for critical decisions"*).
- **Visual**: Interactive 12-node D3 force-directed reasoning graph renders with node pulse animations and glowing relationship paths.
- **Narrative**:
  > "We are designing a clinical dashboard. Notice how the graph connects concepts across biology, architecture, engineering, and industrial design. 
  > 
  > For instance, we see *Emergency Triage Color Systems* linked to *Pharmaceutical Packaging* and *Japanese Garden Flow Design*. Clicking any node reveals human-curated historical context and transferable principles marked with `[CURATED]` provenance tags."

---

### 1:15 - 2:00 | Step 2: Reason & Constraint Manipulation (Deterministic Engine)
- **Action**: Open the **Constraints** sidebar tab. Drag **Information Density** to `0.85` and **Accessibility** to `0.90`. Click **Clinical** preset.
- **Visual**: Edge weights immediately recalculate in real-time. Lines connecting high-density nodes (Swiss Rail, Aircraft Cockpit) thicken; organic paths dim. Node sizes update based on recalculated degree centrality.
- **Narrative**:
  > "Watch what happens when we adjust creative constraints. By boosting accessibility and information density, our backend deterministic constraint engine recalculates relationship weights across the entire network. 
  > 
  > This isn't random black-box LLM guessing — every edge modification is a deterministic `[SYSTEM]` calculation based on domain mathematical models."

---

### 2:00 - 2:30 | Step 3: Design & Understand (System Token Evolution & Granite Rationale)
- **Action**: Open **Design System** tab, then click **Explain Reasoning** on a modified edge.
- **Visual**: Live design system tokens update (Base size grows to 17px, Contrast achieves WCAG AAA, button radii sharpen to 2px). The Explainable Panel slides out showing `[RETRIEVED]`, `[SYSTEM]`, and `[AI]` (IBM Granite) reasoning tiers.
- **Narrative**:
  > "The constraint propagation directly drives our design system tokens. Look at how typography scale, padding, and contrast ratios adapt instantly to guarantee WCAG AAA compliance. 
  > 
  > When we ask for an explanation, IBM Granite breaks down *why* these principles apply, giving clinicians and designers complete confidence in every visual token."

---

### 2:30 - 3:00 | Step 4: Export & Real-World Impact
- **Action**: Open **Export Package** tab and click **Download Full Package**.
- **Visual**: JSON tokens file and Markdown summary document download instantly.
- **Narrative**:
  > "Finally, the entire session — tokens, graph topology, constraints, and AI rationale — exports into standard JSON and Markdown. 
  > 
  > Whether in healthcare, aviation, or civic tech, the Creative Reasoning Platform transforms subjective intuition into explainable, production-ready design architecture."

---

## 🏆 Key Takeaways for Judges
1. **Clear Provenance**: `[CURATED]` vs `[SYSTEM]` vs `[AI]` tags guarantee no hallucinations.
2. **Backend Authoritative**: FastAPI owns 100% of business logic; React/D3 handles presentation.
3. **IBM Granite Integration**: Prepared for `watsonx` deployment with clean adapter patterns.
