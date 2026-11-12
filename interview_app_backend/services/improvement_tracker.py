import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from statistics import mean


class ImprovementTracker:
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or "session_history.json"
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        if not Path(self.storage_path).exists():
            self._save_history({})

    def _load_history(self) -> dict:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_history(self, history: dict) -> None:
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=True)

    def record_session(self, session_data: dict) -> None:
        history = self._load_history()
        session_id = session_data.get("session_id", datetime.now().isoformat())
        scores = session_data.get("scores", [])
        if not scores:
            return

        avg_score = self._calc_avg(scores)

        session_record = {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "questions_completed": session_data.get("questions_completed", len(scores)),
            "average_score": round(avg_score, 2),
            "dimensions": self._aggregate_dimensions(scores),
            "role": session_data.get("role", ""),
            "difficulty": session_data.get("difficulty", ""),
        }

        history[session_id] = session_record
        self._save_history(history)

    def _calc_avg(self, scores):
        vals = []
        for e in scores:
            for v in e.values():
                if isinstance(v, (int, float)):
                    vals.append(v)
        return mean(vals) if vals else 0.0

    def _aggregate_dimensions(self, scores):
        if not scores:
            return {}
        dims = set()
        for e in scores:
            dims.update(e.keys())
        agg = {}
        for d in dims:
            vs = [e.get(d, 0) for e in scores if d in e and isinstance(e.get(d), (int, float))]
            if vs:
                agg[d] = round(mean(vs), 2)
        return agg

    def get_trend(self, dimension: Optional[str] = None):
        history = self._load_history()
        sessions = sorted(history.values(), key=lambda x: x.get("timestamp", ""), reverse=True)
        if not sessions:
            return []

        if dimension:
            return [
                {"session": s.get("session_id"), "score": s.get("dimensions", {}).get(dimension, 0)}
                for s in sessions
                if dimension in s.get("dimensions", {})
            ]

        return [
            {"session": s.get("session_id"), "average": s.get("average_score", 0), "questions": s.get("questions_completed", 0)}
            for s in sessions
        ]

    def calculate_improvement(self):
        history = self._load_history()
        sessions = sorted(history.values(), key=lambda x: x.get("timestamp", ""))
        if len(sessions) < 2:
            return {"trend": "insufficient_data", "sessions_tracked": len(sessions), "overall_change": 0.0}

        first = sessions[0].get("average_score", 0)
        last = sessions[-1].get("average_score", 0)
        change = last - first

        trend = "improving" if change > 0.5 else "declining" if change < -0.5 else "stable"

        return {
            "trend": trend,
            "sessions_tracked": len(sessions),
            "overall_change": round(change, 2),
            "first_session_score": first,
            "last_session_score": last,
        }

    def get_best_session(self):
        history = self._load_history()
        if not history:
            return None
        return max(history.values(), key=lambda x: x.get("average_score", 0))

    def clear_history(self):
        self._save_history({})