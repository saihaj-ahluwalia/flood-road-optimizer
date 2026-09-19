"""
AquaRoute AI - Step 3: Bottleneck Detection & Choke Point Analysis
Identifies saturated corridors (Volume-to-Capacity ratio > 1.0),
critical bridges with zero bypass redundancy, and isolated cutoff nodes.
"""

import networkx as nx
from typing import Dict, Any, List, Tuple


class BottleneckDetector:
    """
    Step 3 Engine: Evaluates network stress, capacity overloads,
    and isolates high-risk failure points.
    """

    def __init__(self, capacity_overload_threshold: float = 1.15):
        self.capacity_threshold = capacity_overload_threshold

    def analyze_bottlenecks(self, G: nx.DiGraph) -> Tuple[nx.DiGraph, List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Analyzes edges for volume-to-capacity saturation and nodes for isolation risk.
        Returns updated graph, edge bottleneck list, and node choke points list.
        """
        edge_bottlenecks = []
        node_choke_points = []

        # 1. Edge Bottleneck Analysis
        for u, v, data in G.edges(data=True):
            capacity = data.get("capacity", 2000)
            flow = data.get("evacuation_flow_volume", 0)
            depth = data.get("flood_depth_m", 0.0)
            is_bridge = data.get("is_bridge", False)

            # Capacity-to-Volume Ratio (CVR)
            cvr = round(flow / max(100, capacity), 2)
            data["cvr"] = cvr

            # Determine bottleneck severity
            is_bottleneck = False
            severity = "normal"
            reason = ""

            if cvr >= 1.8:
                severity = "extreme"
                is_bottleneck = True
                reason = f"Severe traffic surge ({flow} veh vs {capacity} cap, CVR {cvr}x)"
            elif cvr >= 1.2:
                severity = "high"
                is_bottleneck = True
                reason = f"Capacity exceeded ({flow} veh vs {capacity} cap, CVR {cvr}x)"
            elif is_bridge and flow > 1500 and depth > 0.15:
                severity = "high"
                is_bottleneck = True
                reason = "Critical bridge corridor with high flow under waterlogged conditions"
            elif depth >= 0.50 and flow > 500:
                severity = "moderate"
                is_bottleneck = True
                reason = f"Flooded arterial ({depth}m water) carrying active evacuation flow"

            data["is_bottleneck"] = is_bottleneck
            data["bottleneck_severity"] = severity
            data["bottleneck_reason"] = reason

            if is_bottleneck:
                edge_bottlenecks.append({
                    "edge_id": data.get("id", f"{u}_{v}"),
                    "name": data.get("name", "Unnamed Road"),
                    "u": u,
                    "v": v,
                    "cvr": cvr,
                    "flow_volume": flow,
                    "capacity": capacity,
                    "flood_depth_m": depth,
                    "is_bridge": is_bridge,
                    "severity": severity,
                    "reason": reason,
                    "coordinates": data.get("geometry", [])
                })

        # 2. Node Cutoff & Bridge Choke Point Analysis
        # Check node degree before vs after removing submerged edges
        submerged_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("flood_depth_m", 0) >= 0.60]
        G_dry = G.copy()
        G_dry.remove_edges_from(submerged_edges)

        for node_id, data in G.nodes(data=True):
            orig_degree = G.degree(node_id)
            dry_degree = G_dry.degree(node_id)
            node_depth = data.get("flood_depth_m", 0.0)

            # Degree loss fraction
            degree_loss = (orig_degree - dry_degree) / max(1, orig_degree)
            data["degree_loss_pct"] = round(degree_loss * 100, 1)

            # Calculate incoming flow to node
            in_flow = sum(G[p][node_id].get("evacuation_flow_volume", 0) for p in G.predecessors(node_id))
            data["total_inflow"] = in_flow

            # High risk choke points
            if degree_loss >= 0.50 or (in_flow > 4000 and node_depth > 0.20):
                choke_type = "Cutoff Risk Hub" if degree_loss >= 0.66 else "High-Flow Confluence"
                node_choke_points.append({
                    "node_id": node_id,
                    "name": data.get("name", node_id),
                    "lat": data["lat"],
                    "lon": data["lon"],
                    "elevation_m": data.get("elevation", 5.0),
                    "flood_depth_m": node_depth,
                    "degree_loss_pct": round(degree_loss * 100, 1),
                    "in_flow_vehicles": in_flow,
                    "type": choke_type,
                    "severity": "critical" if degree_loss >= 0.75 else "warning"
                })

        # Sort bottlenecks by severity
        edge_bottlenecks.sort(key=lambda x: (x["cvr"], x["flow_volume"]), reverse=True)
        node_choke_points.sort(key=lambda x: (x["degree_loss_pct"], x["in_flow_vehicles"]), reverse=True)

        return G, edge_bottlenecks, node_choke_points
