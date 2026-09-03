# RePackAI — Recommendation Engine

The core recommender system uses a hybrid model that evaluates safety constraints first, performs financial and environmental optimization, overlays ML classifier predictions, and decides on the final disposition recommendation.

## Hybrid Scoring Methodology

For every candidate action $a \in \{\text{RESELL}, \text{REPAIR}, \text{REFURBISH}, \text{RECYCLE}, \text{DISPOSE}\}$ not prohibited by the Rule Engine, a composite score is computed:

$$\text{final\_score}(a) = w_{\text{fin}} \cdot S_{\text{fin}}(a) + w_{\text{env}} \cdot S_{\text{env}}(a) + w_{\text{re}} \cdot S_{\text{re}}(a) + w_{\text{op}} \cdot S_{\text{op}}(a)$$

Where:
*   $w_{\text{fin}}$ = 0.40 (Financial weight)
*   $w_{\text{env}}$ = 0.30 (Environmental weight)
*   $w_{\text{re}}$ = 0.20 (Reusability weight)
*   $w_{\text{op}}$ = 0.10 (Operational complexity weight)

### 1. Financial Score ($S_{\text{fin}}$)
Calculated by normalizing the net financial recovery value of the candidate action relative to all other actions:
$$S_{\text{fin}}(a) = \frac{\text{net\_value}(a) - \min_{a'} \text{net\_value}(a')}{\max_{a'} \text{net\_value}(a') - \min_{a'} \text{net\_value}(a')}$$

### 2. Environmental Score ($S_{\text{env}}$)
Calculated by normalizing the carbon offset of the action relative to other actions:
$$S_{\text{env}}(a) = \frac{\text{carbon\_avoided}(a) - \min_{a'} \text{carbon\_avoided}(a')}{\max_{a'} \text{carbon\_avoided}(a') - \min_{a'} \text{carbon\_avoided}(a')}$$

### 3. Reusability Score ($S_{\text{re}}$)
Standard weight promoting packaging reuse over downcycling and landfill pathways:
*   `RESELL`: 1.0
*   `REPAIR`: 0.8
*   `REFURBISH`: 0.6
*   `RECYCLE`: 0.2
*   `DISPOSE`: 0.0

### 4. Operational Score ($S_{\text{op}}$)
Reflects handling complexity (actions requiring complex material handling have lower operational scores):
*   `RESELL`: 1.0 (Highly standardized, immediate release)
*   `DISPOSE`: 0.9 (Standard disposal, simple handoff)
*   `RECYCLE`: 0.7 (Standard local sorting)
*   `REFURBISH`: 0.5 (Washing, chemical treatment required)
*   `REPAIR`: 0.4 (Manual replacement of panels/welding required)

## Safety Overrides

If any deterministic safety rule is triggered (e.g., Unsafe Structural Condition), the corresponding action scores are forced to $-1.0$.

## ML Model Integration

The ML Model provides a classifier prediction representing historical operator selections.
*   **Recommendation Match**: If the scoring engine's top action matches the ML prediction, confidence is boosted:
    $$\text{confidence} = 0.70 \cdot \text{ML\_confidence} + 0.30 \cdot \text{final\_score}$$
*   **Recommendation Mismatch**: If they do not match, confidence is discounted:
    $$\text{confidence} = 0.50 \cdot \text{ML\_confidence}$$
