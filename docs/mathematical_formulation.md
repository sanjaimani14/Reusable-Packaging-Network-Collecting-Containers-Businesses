# Mathematical Formulation of Multi-Criteria Disposition Optimization

**Project**: RePackAI Reusable Packaging Network  
**Author**: RePackAI Core Team  
**Subject**: Multi-Criteria Decision Analysis (MCDA), Safety Hard-Gates, and Objective Formulations  

---

## 1. Problem Formulation Overview

Given a returned reusable container $c \in \mathcal{C}$ characterized by material $m(c)$, tare weight $w(c)$ (in kg), age $a(c)$ (in months), cumulative trip cycles $u(c)$, and an inspection report $i(c)$, the optimization objective is to select an optimal disposition pathway $d^* \in \mathcal{D}$ where:

$$\mathcal{D} = \{\text{RESELL}, \text{REPAIR}, \text{REFURBISH}, \text{RECYCLE}, \text{DISPOSE}, \text{MANUAL\_REVIEW}\}$$

The objective balances financial recovery, circular economy waste diversion, lifecycle greenhouse gas (GHG) carbon offsets, and operational feasibility, subject to **non-negotiable structural and bio-chemical safety hard gates**.

---

## 2. Safety Hard Gate Formulation (Constraint Set)

In standard weighted scoring, an algorithm could theoretically assign a high economic score to a damaged, high-value container and recommend resale despite life-safety hazards. To categorically prevent catastrophic field failures, safety is formulated as a **strict logical hard-gate constraint** $\mathcal{S}(d)$ rather than a soft additive penalty:

Let binary flags represent inspection findings:
- $unsafe\_structure(i) \in \{0, 1\}$: 1 if structural integrity is compromised (e.g. cracked base, buckled sidewall, or `Unsafe`/`Critical`).
- $hazardous\_contam(i) \in \{0, 1\}$: 1 if toxic, chemical, or bio-hazardous contamination is identified.
- $recyclable(c) \in \{0, 1\}$: 1 if container material is recyclable in existing municipal/commercial streams.
- $completeness(i) \in [0.0, 1.0]$: fraction of required inspection attributes present.

The feasible action space $\mathcal{D}_{feasible}(c, i) \subseteq \mathcal{D}$ is governed by:

$$\mathcal{D}_{feasible} = \begin{cases}
\{\text{MANUAL\_REVIEW}\} & \text{if } completeness(i) < \theta_{comp} \\
\{\text{RECYCLE}, \text{DISPOSE}\} \setminus \{\text{RECYCLE} \mid recyclable(c)=0 \lor hazardous\_contam(i)=1\} & \text{if } unsafe\_structure(i) = 1 \lor hazardous\_contam(i) = 1 \\
\mathcal{D} \setminus \{\text{RECYCLE} \mid recyclable(c)=0\} & \text{otherwise}
\end{cases}$$

Where completeness threshold $\theta_{comp} = 0.80$.

> **Why Safety is a Hard Gate vs. Weighted Factor**:  
> In industrial operations, human physical safety, hazardous material containment regulations (OSHA / ISO 22000), and corporate liability are zero-tolerance constraints. If safety were merely a weighted penalty ($w_s \cdot S$), an extremely high resale value (e.g., ₹5,000 for a specialized stainless steel drum) could overpower the negative penalty, leading to an automated recommendation to resell an exploding or structurally compromised container. Hard-gating guarantees that $\forall d \in \{\text{RESELL}, \text{REPAIR}, \text{REFURBISH}\}$, $P(\text{selected} \mid unsafe\_structure=1) \equiv 0$.

---

## 3. Financial Net Recovery Value (NRV)

For each allowable candidate action $d \in \mathcal{D}_{feasible}$, the Net Recovery Value $\text{NRV}(d)$ is calculated as the expected gross economic recovery minus direct operational processing costs:

$$\text{NRV}(d) = \text{Revenue}(d) - \text{RepairCost}(d) - \text{RefurbCost}(d) - \text{ProcessingCost}(d) - \text{DisposalCost}(d)$$

Explicitly, for each disposition pathway:

1. **RESELL**:
   $$\text{NRV}(\text{RESELL}) = V_{resale}(c, i)$$
   Where $V_{resale} = V_{base}(c) \cdot \max\left(0.1, 1.0 - \frac{a(c)}{60}\cdot 0.6 - \frac{u(c)}{150}\cdot 0.3\right)$.

2. **REPAIR**:
   $$\text{NRV}(\text{REPAIR}) = V_{resale}(c, i) - C_{repair}(i)$$

3. **REFURBISH**:
   $$\text{NRV}(\text{REFURBISH}) = V_{resale}(c, i) - C_{refurb}(i)$$
   Where $C_{refurb}(i) = 0.15 \cdot V_{base}(c) + 0.15 \cdot (100 - Score_{clean}(i)) + 0.08 \cdot u(c)$.

4. **RECYCLE**:
   $$\text{NRV}(\text{RECYCLE}) = \left(w(c) \cdot R_{recycle}(m)\right) - \left(w(c) \cdot C_{proc}(m)\right)$$
   Where $R_{recycle}(m)$ is the scrap material market value per kg, and $C_{proc}(m)$ is sorting/grinding processing cost.

5. **DISPOSE**:
   $$\text{NRV}(\text{DISPOSE}) = - C_{disposal}(c, i) = - \left(5.0 + 0.25 \cdot w(c)\right) \cdot M_{contam}(i)$$
   Where $M_{contam} = 6.0$ for hazardous, $2.5$ for chemical, and $1.0$ for non-hazardous waste.

Normalized financial utility $V(d) \in [0, 1]$ is:

$$V(d) = \frac{\text{NRV}(d) - \min_{k \in \mathcal{D}}\text{NRV}(k)}{\max_{k \in \mathcal{D}}\text{NRV}(k) - \min_{k \in \mathcal{D}}\text{NRV}(k)}$$

---

## 4. Environmental Impact & Waste Avoided

### 4.1 Solid Waste Diverted ($W(d)$)
Represents the physical mass of material saved from municipal landfills:

$$W(d) = \begin{cases}
w(c) & \text{for } d \in \{\text{RESELL}, \text{REPAIR}, \text{REFURBISH}\} \\
0.80 \cdot w(c) & \text{for } d = \text{RECYCLE} \quad (80\% \text{ secondary recovery efficiency}) \\
0.0 & \text{for } d \in \{\text{DISPOSE}, \text{MANUAL\_REVIEW}\}
\end{cases}$$

### 4.2 Greenhouse Gas Carbon Footprint Offset ($E(d)$)
Measures the net avoided cradle-to-gate greenhouse gas emissions (in kg $\text{CO}_2\text{e}$) calculated relative to virgin material production displacement:

$$E(d) = E_{virgin}(c) - E_{processing}(d)$$

Where:
- $E_{virgin}(c) = w(c) \cdot e_{factor}(m)$  
  Emission factors ($e_{factor}$): Cardboard = $1.0$, Wood = $0.4$, HDPE Plastic = $2.6$, Galvanized Steel = $5.5\text{ kg CO}_2\text{e/kg}$.
- $E_{processing}(\text{RESELL}) = w(c) \cdot 0.02$ (inspection/handling)
- $E_{processing}(\text{REPAIR}) = w(c) \cdot 0.12 + \Delta_{damage}$
- $E_{processing}(\text{REFURBISH}) = w(c) \cdot 0.25 + 0.8$ (hot water/chemical wash)
- $E_{processing}(\text{RECYCLE}) = 0.40 \cdot E_{virgin}(c)$
- $E_{processing}(\text{DISPOSE}) = 1.20 \cdot E_{virgin}(c)$ (landfill methane generation and transport)

Normalized carbon utility $E_{norm}(d) \in [0, 1]$ is:

$$E_{norm}(d) = \frac{E(d) - \min_{k \in \mathcal{D}}E(k)}{\max_{k \in \mathcal{D}}E(k) - \min_{k \in \mathcal{D}}E(k)}$$

---

## 5. Circular Economy & Operational Feasibility Hierarchy

To favor high-circularity reuse loops over mechanical downcycling, a Circularity Reusability score $R(d)$ and Operational Simplicity score $O(d)$ are defined:

| Action Pathway $d$ | Reusability $R(d)$ | Operational Feasibility $O(d)$ | Description |
| :--- | :---: | :---: | :--- |
| **RESELL** | $1.0$ | $1.0$ | Direct redeployment with zero reprocessing delay. |
| **REPAIR** | $0.8$ | $0.4$ | Restores original utility; requires labor/parts. |
| **REFURBISH** | $0.6$ | $0.5$ | Intensive cleaning and cosmetic renewal. |
| **RECYCLE** | $0.2$ | $0.7$ | Breaks down into pellets/shreds; downcycled. |
| **DISPOSE** | $0.0$ | $0.9$ | Permanent landfill/incineration; simple haulage. |

---

## 6. Multi-Criteria Composite Scoring Function

For each feasible action $d \in \mathcal{D}_{feasible}$, the overall multi-criteria utility score $Score(d)$ is defined by the weighted linear combination:

$$Score(d) = w_{fin} \cdot V(d) + w_{env} \cdot E_{norm}(d) + w_{re} \cdot R(d) + w_{op} \cdot O(d)$$

Subject to weight simplex constraints:
$$w_{fin} + w_{env} + w_{re} + w_{op} = 1.0, \quad w_j \ge 0$$

Default validated system configuration:
- $w_{fin} = 0.40$ (Financial Viability)
- $w_{env} = 0.30$ (Lifecycle Decarbonization)
- $w_{re} = 0.20$ (Circular Economy Preservation)
- $w_{op} = 0.10$ (Operational Turnaround Feasibility)

The recommended disposition $d^*$ is given by:

$$d^* = \arg\max_{d \in \mathcal{D}_{feasible}} Score(d)$$

---

## 7. Decision Escalation Thresholds & Confidence

The final output is augmented with a hybrid confidence rating $\mathcal{C}(d^*)$ combining Machine Learning alignment $\mathcal{C}_{ml}$ and score separation margin:

$$\mathcal{C}(d^*) = \begin{cases}
\text{clip}\left(0.70 \cdot \mathcal{C}_{ml} + 0.30 \cdot Score(d^*), 0.0, 1.0\right) & \text{if } d^*_{ml} = d^* \\
\text{clip}\left(0.50 \cdot \mathcal{C}_{ml}, 0.0, 1.0\right) & \text{if } d^*_{ml} \ne d^*
\end{cases}$$

Human confirmation (`PENDING_HUMAN_CONFIRMATION`) is required if:
1. $d^* = \text{DISPOSE}$ (preventing accidental destruction of reusable assets), OR
2. $\mathcal{C}(d^*) < \tau_{conf} = 0.60$, OR
3. $safety\_risk(i) = \text{"High"}$, OR
4. $completeness(i) < \theta_{comp} = 0.80$.

---

## 8. Baseline Heuristic Formulation for Comparative Benchmark

The simplified baseline heuristic follows a traditional sequential greedy decision tree:

$$d_{baseline} = \begin{cases}
\text{MANUAL\_REVIEW} & \text{if } completeness < 0.80 \\
\text{RECYCLE} & \text{else if } is\_unsafe = 1 \land recyclable = 1 \\
\text{DISPOSE} & \text{else if } is\_unsafe = 1 \land recyclable = 0 \\
\text{RESELL} & \text{else if } damage = \text{"None"} \land repair\_cost = 0 \land resale\_value > 0 \\
\text{REPAIR} & \text{else if } repair\_cost < resale\_value \land repair\_cost > 0 \\
\text{REFURBISH} & \text{else if } refurb\_cost < resale\_value \land refurb\_cost > 0 \\
\text{RECYCLE} & \text{else if } recyclable = 1 \\
\text{DISPOSE} & \text{otherwise}
\end{cases}$$

**Key Differentiation**: While the baseline considers only pairwise cost inequalities, the proposed MCDA system integrates multi-criteria emissions, carbon avoidance, reusability indexing, and ML cross-validation, capturing higher recovery value and eliminating suboptimal recycling of easily repairable containers.
