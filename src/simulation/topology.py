"""Circuit topology — wiring clusters determine which panels contribute."""

from collections import defaultdict
from typing import Dict, List, Set


def _connected_components(adj: Dict[str, Set[str]]) -> List[List[str]]:
    visited: Set[str] = set()
    clusters: List[List[str]] = []
    for start in adj:
        if start in visited:
            continue
        stack = [start]
        comp: List[str] = []
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            comp.append(node)
            for nb in adj[node]:
                if nb not in visited:
                    stack.append(nb)
        clusters.append(comp)
    return clusters


def analyze_topology(
    panels: List[dict],
    batteries: List[dict],
    connections: List[dict],
    *,
    require_battery_link: bool = True,
) -> dict:
    """
    Determine effective PV capacity from how components are wired.

    Rules (require_battery_link=True):
    - Only panels in the same connected component as at least one battery produce.
    - Isolated panels (no wires) do not produce.
    - Panel-only wired groups without a battery do not produce.
    """
    panel_by_id = {p["instance_id"]: p for p in panels}
    battery_by_id = {b["instance_id"]: b for b in batteries}
    all_ids = set(panel_by_id) | set(battery_by_id)

    adj: Dict[str, Set[str]] = {nid: set() for nid in all_ids}
    for wire in connections:
        a, b = wire.get("source_id"), wire.get("target_id")
        if a in adj and b in adj:
            adj[a].add(b)
            adj[b].add(a)

    for nid in all_ids:
        if not connections and not require_battery_link:
            continue

    active_panel_ids: Set[str] = set()
    active_battery_ids: Set[str] = set()
    orphan_panels = 0
    idle_wired_panels = 0

    if not require_battery_link:
        active_panel_ids = set(panel_by_id)
        active_battery_ids = set(battery_by_id)
    elif not connections:
        orphan_panels = len(panel_by_id)
    else:
        for comp in _connected_components(adj):
            comp_panels = [n for n in comp if n in panel_by_id]
            comp_batteries = [n for n in comp if n in battery_by_id]
            if not comp_panels and not comp_batteries:
                continue
            if not comp_panels:
                continue
            if len(comp) == 1:
                orphan_panels += len(comp_panels)
                continue
            if comp_batteries:
                active_panel_ids.update(comp_panels)
                active_battery_ids.update(comp_batteries)
            else:
                idle_wired_panels += len(comp_panels)

    effective_pv_w = sum(
        float(panel_by_id[pid].get("rated_power_w", 0))
        for pid in active_panel_ids
    )
    effective_battery_wh = sum(
        float(battery_by_id[bid].get("capacity_wh", 0))
        for bid in active_battery_ids
    )

    return {
        "effective_pv_w": effective_pv_w,
        "effective_battery_wh": effective_battery_wh,
        "active_panel_count": len(active_panel_ids),
        "total_panel_count": len(panel_by_id),
        "orphan_panels": orphan_panels,
        "idle_wired_panels": idle_wired_panels,
        "cluster_count": len(_connected_components(adj)) if all_ids else 0,
        "wired_cluster_count": len([
            c for c in _connected_components(adj)
            if any(n in battery_by_id for n in c)
        ]) if all_ids else 0,
    }
