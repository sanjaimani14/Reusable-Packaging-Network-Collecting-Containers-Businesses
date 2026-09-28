# Backward compatibility wrapper for recommender_rules
try:
    from repackai.backend.app.recommender_rules.engine import RuleEngine, RuleResult
except ImportError:
    try:
        from backend.app.recommender_rules.engine import RuleEngine, RuleResult
    except ImportError:
        from app.recommender_rules.engine import RuleEngine, RuleResult

__all__ = ["RuleEngine", "RuleResult"]
