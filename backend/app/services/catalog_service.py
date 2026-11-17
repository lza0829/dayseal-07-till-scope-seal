from __future__ import annotations
from typing import Any
from app.db import connect
from app.repositories import closes as close_repo
from app.repositories import lines as line_repo
from app.repositories import settings as settings_repo
from app.repositories import tills as till_repo
from app.services.close_service import STRATEGY_STORE


def dashboard() -> dict[str, Any]:
    conn = connect()
    try:
        day = settings_repo.get(conn, "business_day") or ""
        strategy = settings_repo.get(conn, "close_strategy") or STRATEGY_STORE
        total, count = line_repo.day_total(conn, day) if day else (0.0, 0)
        day_batch = close_repo.get_day_batch(conn, day) if day else None
        day_sealed = day_batch is not None
        sealed_tills = close_repo.sealed_till_codes(conn, day) if day else set()
        active_tills = line_repo.active_till_codes(conn, day) if day else set()
        till_count = len(till_repo.list_tills(conn))
        # 分机策略下日封前置：当日活跃机是否全部已机封
        all_tills_sealed = active_tills.issubset(sealed_tills) if day else True
        return {
            "business_day": day,
            "close_strategy": strategy,
            "till_count": till_count,
            "line_count_today": count,
            "system_total_today": round(float(total), 2),
            "sealed_today": day_sealed,
            "active_till_count": len(active_tills),
            "sealed_till_count": len(sealed_tills),
            "all_tills_sealed": all_tills_sealed,
            "close_batch_count": conn.execute("SELECT COUNT(*) c FROM close_batches").fetchone()["c"],
            "open_variance_count": conn.execute(
                "SELECT COUNT(*) c FROM variance_rows WHERE disposition='pending'"
            ).fetchone()["c"],
        }
    finally:
        conn.close()
