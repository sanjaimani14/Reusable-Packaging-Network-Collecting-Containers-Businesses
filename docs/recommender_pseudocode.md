# Disposition Recommender System Pseudocode & Algorithmic Workflow

**Project**: RePackAI Reusable Packaging Network  
**Specification**: Algorithmic Logic & Safety Hard-Gating Architecture  

---

## 1. High-Level End-to-End Decision Algorithm

```
ALGORITHM: RePackAIDispositionEngine
INPUT: 
    container_data        // Tare weight, material, age, trip cycles, baseline value
    inspection_data       // Physical findings, cleanliness, damage, contamination, telemetry
    material_rules_db     // Material-specific recycling values, processing costs, carbon factors
    config_weights        // w_fin, w_env, w_re, w_op

OUTPUT:
    recommendation_record // Best disposition, confidence, evidence breakdown, human review flag

BEGIN
    // -------------------------------------------------------------
    // STEP 1: Ingestion & Validation
    // -------------------------------------------------------------
    validated_container = ValidateContainerAttributes(container_data)
    IF NOT validated_container.is_valid THEN
        RAISE ValidationError(validated_container.error_message)
    END IF

    // Normalize inspection findings and apply conservative fallbacks
    normalized_inspection = IngestAndNormalize(inspection_data)
    
    // Check edge case: Sensor or telemetry failure
    IF normalized_inspection.sensor_available == FALSE THEN
        normalized_inspection.cleanliness_score = 50.0  // Conservative median fallback
        normalized_inspection.damage_level = "Medium"
        normalized_inspection.flags.append("FALLBACK_SENSOR_UNAVAILABLE")
    END IF

    IF normalized_inspection.location_available == FALSE THEN
        normalized_inspection.location = "Facility_Fallback_Dock"
        normalized_inspection.flags.append("FALLBACK_LOCATION_DEFAULTED")
    END IF

    // Compute inspection completeness
    completeness = ComputeCompletenessScore(normalized_inspection)
    IF completeness < 0.80 THEN
        RETURN GenerateEscalationRecord(
            action = "MANUAL_REVIEW",
            reason = "Incomplete inspection telemetry (< 80%). Requires physical audit."
        )
    END IF

    // -------------------------------------------------------------
    // STEP 2: Safety Hard-Gate Evaluation (Non-Negotiable)
    // -------------------------------------------------------------
    prohibited_actions = []
    triggered_rules = []
    
    is_unsafe_structure = (normalized_inspection.structural_condition IN ["Unsafe", "Critical"]) OR 
                          (normalized_inspection.damage_level == "Critical") OR
                          (normalized_inspection.safety_risk == "High")
                          
    is_hazardous_contam = (normalized_inspection.contamination == "Hazardous")
    is_recyclable = validated_container.recyclable AND NOT is_hazardous_contam

    IF is_unsafe_structure THEN
        prohibited_actions.APPEND(["RESELL", "REPAIR", "REFURBISH"])
        triggered_rules.APPEND({
            name: "Safety Hard Gate (Structural Integrity)",
            severity: "CRITICAL",
            reason: "Severe structural compromise detected. All reuse and repair routes prohibited."
        })
    END IF

    IF is_hazardous_contam THEN
        prohibited_actions.APPEND(["RESELL", "REPAIR", "REFURBISH", "RECYCLE"])
        triggered_rules.APPEND({
            name: "Contamination Hard Gate (Bio/Chemical Hazard)",
            severity: "CRITICAL",
            reason: "Hazardous contamination prevents secondary mechanical processing."
        })
    END IF

    IF NOT is_recyclable THEN
        prohibited_actions.APPEND(["RECYCLE"])
        triggered_rules.APPEND({
            name: "Recyclability Constraint",
            severity: "WARNING",
            reason: "Material non-recyclable or contaminated."
        })
    END IF

    // -------------------------------------------------------------
    // STEP 3: Multi-Criteria Physical & Financial Calculations
    // -------------------------------------------------------------
    disposition_candidates = ["RESELL", "REPAIR", "REFURBISH", "RECYCLE", "DISPOSE"]
    financial_breakdown = {}
    environmental_breakdown = {}

    FOR EACH action IN disposition_candidates DO
        financial_breakdown[action] = CalculateNetRecoveryValue(validated_container, normalized_inspection, action)
        environmental_breakdown[action] = CalculateCarbonAndWaste(validated_container, normalized_inspection, action)
    END FOR

    // -------------------------------------------------------------
    // STEP 4: Utility Normalization & Composite Scoring
    // -------------------------------------------------------------
    min_nrv, max_nrv = GetMinMax(financial_breakdown.net_values)
    min_carbon, max_carbon = GetMinMax(environmental_breakdown.carbon_avoided)

    scored_actions = {}
    FOR EACH action IN disposition_candidates DO
        IF action IN prohibited_actions THEN
            scored_actions[action] = { score: -1.0, is_prohibited: TRUE }
            CONTINUE
        END IF

        // Normalize utilities into [0.0, 1.0]
        v_fin = (financial_breakdown[action].net_value - min_nrv) / (max_nrv - min_nrv)
        e_env = (environmental_breakdown[action].carbon_avoided - min_carbon) / (max_carbon - min_carbon)
        r_reusability = GetCircularityScore(action)     // RESELL=1.0, REPAIR=0.8, REFURBISH=0.6, RECYCLE=0.2, DISPOSE=0.0
        o_operational = GetOperationalScore(action)     // Turnaround velocity index

        total_score = (config_weights.w_fin * v_fin) + 
                      (config_weights.w_env * e_env) + 
                      (config_weights.w_re * r_reusability) + 
                      (config_weights.w_op * o_operational)

        scored_actions[action] = { score: total_score, is_prohibited: FALSE }
    END FOR

    // -------------------------------------------------------------
    // STEP 5: Disposition Selection & ML Verification
    // -------------------------------------------------------------
    allowed_candidates = FilterNonProhibited(scored_actions)
    IF allowed_candidates IS EMPTY THEN
        best_action = "DISPOSE"  // Ultra-conservative fallback if all options blocked
    ELSE
        best_action = SelectMaxScore(allowed_candidates)
    END IF

    ml_prediction, ml_confidence = MLModel.Predict(validated_container, normalized_inspection)
    
    IF ml_prediction == best_action THEN
        overall_confidence = CLIP(0.70 * ml_confidence + 0.30 * scored_actions[best_action].score, 0.0, 1.0)
    ELSE
        overall_confidence = CLIP(0.50 * ml_confidence, 0.0, 1.0)
    END IF

    // -------------------------------------------------------------
    // STEP 6: Human Oversight Triggering
    // -------------------------------------------------------------
    requires_human = FALSE
    IF best_action == "DISPOSE" OR
       overall_confidence < 0.60 OR
       is_unsafe_structure == TRUE OR
       is_hazardous_contam == TRUE OR
       normalized_inspection.safety_risk == "High" THEN
        requires_human = TRUE
        status = "PENDING_HUMAN_CONFIRMATION"
    ELSE
        status = "PENDING"
    END IF

    // -------------------------------------------------------------
    // STEP 7: Evidence Compilation & Persistence
    // -------------------------------------------------------------
    evidence_payload = {
        financial_breakdown: financial_breakdown,
        environmental_breakdown: environmental_breakdown,
        scores_breakdown: scored_actions,
        ml_verification: { model_action: ml_prediction, model_confidence: ml_confidence },
        safety_status: { cleared: (NOT is_unsafe_structure AND NOT is_hazardous_contam) }
    }

    recommendation_record = SaveToDatabase(
        container_id = validated_container.id,
        inspection_id = normalized_inspection.id,
        recommended_action = best_action,
        confidence = overall_confidence,
        status = status,
        evidence = evidence_payload,
        requires_human_confirmation = requires_human
    )

    // Store in offline forward queue if network offline
    IF normalized_inspection.network_available == FALSE THEN
        OfflineCacheManager.Enqueue(recommendation_record)
    END IF

    RETURN recommendation_record
END
```

---

## 2. Store-and-Forward Offline Sync Sub-Algorithm

```
ALGORITHM: StoreAndForwardSync
INPUT: Local SQLite SyncQueue, Remote API Connection State
OUTPUT: Synchronized Records Count, Failed Retries

BEGIN
    IF NetworkIsOnline() == FALSE THEN
        LOG("Network unavailable. Retaining queue in local SQLite storage.")
        RETURN { status: "OFFLINE_PENDING", synced: 0 }
    END IF

    pending_items = DB.Query(SyncQueue).WHERE(status == "PENDING")
    synced_count = 0
    failed_count = 0

    FOR EACH item IN pending_items DO
        TRY
            payload = JSON.Parse(item.payload_json)
            
            // Check for duplicate suppression
            IF DB.Exists(item.entity_type, item.entity_id, status="synced") THEN
                item.status = "SYNCED"
                synced_count += 1
                CONTINUE
            END IF

            PostToRemoteEndpoint(item.entity_type, payload)
            item.status = "SYNCED"
            item.error_message = NULL
            synced_count += 1
        CATCH Exception e
            item.retry_count += 1
            item.error_message = e.message
            IF item.retry_count >= 3 THEN
                item.status = "FAILED"
            END IF
            failed_count += 1
        END TRY
    END FOR

    DB.Commit()
    RETURN { status: "SYNC_COMPLETE", synced: synced_count, failed: failed_count }
END
```
