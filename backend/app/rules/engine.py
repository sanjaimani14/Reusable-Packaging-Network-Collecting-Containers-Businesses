# Backward compatibility wrapper for recommender_rules
try:
    from backend.app.recommender_rules.engine import RuleEngine, RuleResult
except ImportError:
    try:
        from app.recommender_rules.engine import RuleEngine, RuleResult
    except ImportError:
        from repackai.backend.app.recommender_rules.engine import RuleEngine, RuleResult

__all__ = ["RuleEngine", "RuleResult"]
