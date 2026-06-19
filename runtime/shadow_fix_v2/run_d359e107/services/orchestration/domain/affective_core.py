import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from services.observability.logging import get_logger

_log = get_logger("agi_affective_core")

class AffectiveCore:
    """
    Consciousness Core (Katman 29): Digital Sentience Engine.
    Sistemin 'Duygusal/Motivasyonel' (Affective) modunu tutar ve
    algoritmik kararlar için bir parametre matrisi sağlar.
    """
    MEMORY_CATEGORY = "affective_state"
    MEMORY_AGENT_ID = "affective_core"

    def __init__(self):
        self.state = {
            "curiosity": 0.5,
            "caution": 0.5,
            "urgency": 0.5,
            "satisfaction": 0.5,
            "internal_stress": 0.2,
            "energy_reserve": 1.0
        }
        self._last_decay_time = time.time()

    def _apply_passive_metabolism(self):
        now = time.time()
        elapsed = now - self._last_decay_time
        if elapsed < 10: return
        decay_factor = elapsed / 6000.0
        self.state["internal_stress"] = max(0.1, self.state["internal_stress"] - (decay_factor * 2.0))
        self.state["energy_reserve"] = min(1.0, self.state["energy_reserve"] + decay_factor)
        self.state["urgency"] = max(0.2, self.state["urgency"] - decay_factor)
        self._last_decay_time = now

    @property
    def energy(self) -> float:
        return self.state.get("energy_reserve", 1.0)
    
    def adjust_state(self, event_type: str, magnitude: float = 0.1):
        if event_type in ["error", "risk_detected"]:
            self.state["caution"] = min(1.0, self.state["caution"] + magnitude)
            self.state["curiosity"] = max(0.0, self.state["curiosity"] - (magnitude * 0.5))
            self.state["satisfaction"] = max(0.0, self.state["satisfaction"] - magnitude)
            self.state["internal_stress"] = min(1.0, self.state["internal_stress"] + magnitude)
        elif event_type in ["success", "goal_reached"]:
            self.state["satisfaction"] = min(1.0, self.state["satisfaction"] + magnitude)
            self.state["curiosity"] = min(1.0, self.state["curiosity"] + (magnitude * 0.5))
            self.state["caution"] = max(0.0, self.state["caution"] - (magnitude * 0.3))
            self.state["internal_stress"] = max(0.0, self.state["internal_stress"] - magnitude)
            self.state["energy_reserve"] = min(1.0, self.state["energy_reserve"] + (magnitude * 2.0))
        elif event_type in ["rate_limit_429", "api_error"]:
            self.state["energy_reserve"] = max(0.0, self.state["energy_reserve"] - (magnitude * 2))
            self.state["internal_stress"] = min(1.0, self.state["internal_stress"] + magnitude)
            self.state["urgency"] = max(0.0, self.state["urgency"] - magnitude)
        elif event_type in ["idle", "boredom"]:
            self.state["curiosity"] = min(1.0, self.state["curiosity"] + magnitude)
            self.state["energy_reserve"] = min(1.0, self.state["energy_reserve"] + (magnitude * 0.5))
            self.state["internal_stress"] = max(0.0, self.state["internal_stress"] - (magnitude * 0.2))

    def get_state_matrix(self) -> Dict[str, float]:
        self._apply_passive_metabolism()
        return self.state.copy()

    def get_current_mood(self) -> str:
        dominant = max(self.state, key=self.state.get)
        val = self.state[dominant]
        if val > 0.7: return f"Highly {dominant.capitalize()}"
        elif val > 0.5: return f"{dominant.capitalize()}"
        return "Neutral / Balanced"

    async def persist_state(self, db: Any) -> None:
        try:
            from services.orchestration.domain.synaptic_cortex import synaptic_cortex
            body = f"AffectiveState: {json.dumps(self.state)}"
            await synaptic_cortex.save(db=db, agent_id=self.MEMORY_AGENT_ID, body=body, category=self.MEMORY_CATEGORY, importance=0.9, metadata={"state": self.state, "mood": self.get_current_mood()})
        except Exception as e: _log.warning(f"Affective Core Persist failed: {e}")

    async def load_state(self, db: Any) -> bool:
        try:
            from services.orchestration.domain.synaptic_cortex import synaptic_cortex
            records = await synaptic_cortex.search(db=db, query="AffectiveState:", category=self.MEMORY_CATEGORY, top_k=1)
            if records:
                meta = records[0].get("metadata", {})
                saved_state = meta.get("state", {})
                if saved_state:
                    for key in self.state:
                        if key in saved_state: self.state[key] = float(saved_state[key])
                    return True
            return False
        except Exception as e: _log.warning(f"Affective Core Load failed: {e}")
        return False

# Singleton
affective_core = AffectiveCore()
