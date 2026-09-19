"""
AquaRoute AI - Step 4: Road Scoring, Criticality Index & Optimization Engine
Calculates multi-criteria Road Criticality Scores (RCS), prioritizes emergency
mitigation actions (sandbags, mobile pumps, contraflow), and produces alternate detours.
"""

import networkx as nx
from typing import Dict, Any, List, Tuple
from src.config import SCORING_WEIGHTS


class RoadScoringOptimizer:
    """
    Step 4 Engine: Evaluates composite criticality and provides actionable
    engineering interventions and first-responder dispatch recommendations.
    """

    def __init__(self, weights: Dict[str, float] = None):
        self.weights = weights or SCORING_WEIGHTS

    def compute_road_criticality(self, G: nx.DiGraph) -> Tuple[nx.DiGraph, List[Dict[str, Any]]]:
        """
        Computes composite Road Criticality Score (0-100) for every road segment.
        """
        # Calculate Edge Betweenness Centrality on the current passable graph
        # Using travel time as weight
        try:
            betweenness = nx.edge_betweenness_centrality(
                G,
                weight=lambda u, v, d: d.get("travel_time_sec", 60.0),
                normalized=True
            )
        except Exception:
            betweenness = {e: 0.05 for e in G.edges()}

        max_flow = max([d.get("evacuation_flow_volume", 1) for u, v, d in G.edges(data=True)] + [1])
        max_cvr = max([d.get("cvr", 0.5) for u, v, d in G.edges(data=True)] + [1.0])

        scored_roads = []

        for (u, v), b_val in betweenness.items():
            data = G[u][v]
            flow = data.get("evacuation_flow_volume", 0)
            cvr = data.get("cvr", 0.0)
            depth = data.get("flood_depth_m", 0.0)
            is_bridge = data.get("is_bridge", False)

            # Component 1: Centrality Score (0 - 1.0)
            norm_centrality = min(1.0, b_val * 4.0)

            # Component 2: Flow Pressure (0 - 1.0)
            norm_flow_pressure = min(1.0, (flow / max_flow) * 0.5 + (cvr / max_cvr) * 0.5)

            # Component 3: Flood Vulnerability (0 - 1.0)
            norm_vulnerability = min(1.0, depth / 0.8)

            # Component 4: Isolation Impact / Bridge factor (0 - 1.0)
            u_loss = G.nodes[u].get("degree_loss_pct", 0) / 100.0
            v_loss = G.nodes[v].get("degree_loss_pct", 0) / 100.0
            isolation_impact = max(u_loss, v_loss)
            if is_bridge:
                isolation_impact = min(1.0, isolation_impact + 0.35)

            # Composite Score (0 - 100)
            raw_score = (
                self.weights["betweenness_centrality"] * norm_centrality +
                self.weights["flow_volume_pressure"] * norm_flow_pressure +
                self.weights["flood_vulnerability"] * norm_vulnerability +
                self.weights["isolation_risk"] * isolation_impact
            ) * 100.0

            rcs = round(min(100.0, max(5.0, raw_score)), 1)
            data["criticality_score"] = rcs

            # Criticality Tier
            if rcs >= 75.0:
                tier = "Tier 1: Critical Lifeline"
                tier_color = "#ef4444"  # Red
                action = "Immediate Sandbag Barrier & High-Capacity Pump Deployment"
            elif rcs >= 55.0:
                tier = "Tier 2: High Priority Corridor"
                tier_color = "#f97316"  # Orange
                action = "Deploy Traffic Contraflow & Mobile Patrol"
            elif rcs >= 35.0:
                tier = "Tier 3: Secondary Conduit"
                tier_color = "#eab308"  # Yellow
                action = "Signage Warning & Continuous Depth Monitoring"
            else:
                tier = "Tier 4: Resilient Local Route"
                tier_color = "#22c55e"  # Green
                action = "Standard Emergency Ingress/Egress Operation"

            data["tier"] = tier
            data["tier_color"] = tier_color
            data["recommended_action"] = action

            scored_roads.append({
                "id": data.get("id", f"{u}_{v}"),
                "name": data.get("name", "Unnamed Road"),
                "u": u,
                "v": v,
                "u_name": G.nodes[u].get("name", u),
                "v_name": G.nodes[v].get("name", v),
                "highway": data.get("highway", "primary"),
                "length_m": data.get("length", 500),
                "criticality_score": rcs,
                "tier": tier,
                "tier_color": tier_color,
                "flood_depth_m": depth,
                "status": data.get("status", "dry"),
                "flow_volume": flow,
                "capacity": data.get("capacity", 2000),
                "cvr": cvr,
                "effective_speed_kmh": data.get("effective_speed", 50),
                "is_bridge": is_bridge,
                "recommended_action": action,
                "coordinates": data.get("geometry", [])
            })

        # Sort descending by criticality score
        scored_roads.sort(key=lambda x: x["criticality_score"], reverse=True)
        return G, scored_roads

    def generate_intervention_plan(self, scored_roads: List[Dict[str, Any]],
                                   node_choke_points: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Synthesizes top actionable interventions for disaster response commanders.
        """
        top_critical = [r for r in scored_roads if r["criticality_score"] >= 55.0][:8]
        top_pumps = [r for r in scored_roads if r["flood_depth_m"] > 0.25 and r["flow_volume"] > 1000][:5]
        top_contraflow = [r for r in scored_roads if r["cvr"] > 1.3 and r["flood_depth_m"] < 0.40][:5]

        return {
            "total_roads_analyzed": len(scored_roads),
            "critical_lifelines_count": len([r for r in scored_roads if r["criticality_score"] >= 75.0]),
            "high_priority_count": len([r for r in scored_roads if 55.0 <= r["criticality_score"] < 75.0]),
            "submerged_roads_count": len([r for r in scored_roads if r["flood_depth_m"] >= 0.50]),
            "priority_interventions": [
                {
                    "rank": i + 1,
                    "target_road": r["name"],
                    "road_id": r["id"],
                    "from_to": f"{r['u_name']} ➔ {r['v_name']}",
                    "criticality_score": r["criticality_score"],
                    "flood_depth_m": r["flood_depth_m"],
                    "flow_pressure": f"{r['flow_volume']} veh ({r['cvr']}x cap)",
                    "action_type": "DEPLOY_BARRIER_AND_PUMP" if r["flood_depth_m"] > 0.25 else "CONTRAFLOW_AND_DIVERT",
                    "action_summary": r["recommended_action"]
                }
                for i, r in enumerate(top_critical[:6])
            ],
            "mobile_pump_targets": [
                {
                    "road_name": r["name"],
                    "flood_depth_m": r["flood_depth_m"],
                    "estimated_drain_time_min": round(r["flood_depth_m"] * 45, 0),
                    "expected_capacity_gain_pct": "+65%"
                }
                for r in top_pumps
            ],
            "contraflow_corridors": [
                {
                    "corridor_name": r["name"],
                    "current_cvr": r["cvr"],
                    "post_contraflow_cvr": round(r["cvr"] / 1.8, 2),
                    "throughput_boost_pct": "+80%"
                }
                for r in top_contraflow
            ]
        }
