class GovernorAlertConfig:
    DEFAULT_THRESHOLDS = {
        "alerts.accuracy.min": 0.85,
        "alerts.false_positive.multiplier": 1.5,
        "alerts.freeze.max_minutes": 60,
        "alerts.policy_churn.max_per_day": 5
    }

    @classmethod
    def get_threshold(cls, key: str) -> float:
        # Gelecekte GovernorPolicyConfig'den çekebilir
        return cls.DEFAULT_THRESHOLDS.get(key, 0.0)
