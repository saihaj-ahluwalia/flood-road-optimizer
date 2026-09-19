"""
AquaRoute AI - GeoJSON & JSON Scenario Exporter
Serializes simulation results into clean, optimized GeoJSON structures
ready for Leaflet map consumption and dashboard charts.
"""

import json
import os
import networkx as nx
from typing import Dict, Any, List


class ScenarioExporter:
    """
    Serializes simulation graph and metrics into web-ready JSON/GeoJSON files.
    """

    @staticmethod
    def build_web_scenario_payload(
        city_config: Dict[str, Any],
        scenario_key: str,
        scenario_meta: Dict[str, Any],
        G: nx.DiGraph,
        flood_polygons: List[Dict[str, Any]],
        evacuation_routes: List[Dict[str, Any]],
        edge_bottlenecks: List[Dict[str, Any]],
        node_chokes: List[Dict[str, Any]],
        scored_roads: List[Dict[str, Any]],
        interventions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Builds the unified scenario data payload.
        """
        # 1. Roads GeoJSON FeatureCollection
        road_features = []
        for r in scored_roads:
            coords = r.get("coordinates", [])
            if len(coords) >= 2:
                # GeoJSON expects [lon, lat]
                geojson_coords = [[p[1], p[0]] for p in coords]
                road_features.append({
                    "type": "Feature",
                    "id": r["id"],
                    "properties": {
                        "id": r["id"],
                        "name": r["name"],
                        "highway": r["highway"],
                        "from_node": r["u_name"],
                        "to_node": r["v_name"],
                        "criticality_score": r["criticality_score"],
                        "tier": r["tier"],
                        "tier_color": r["tier_color"],
                        "flood_depth_m": r["flood_depth_m"],
                        "status": r["status"],
                        "flow_volume": r["flow_volume"],
                        "capacity": r["capacity"],
                        "cvr": r["cvr"],
                        "speed_kmh": r["effective_speed_kmh"],
                        "is_bridge": r["is_bridge"],
                        "action": r["recommended_action"],
                        "length_m": r["length_m"]
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": geojson_coords
                    }
                })

        roads_geojson = {
            "type": "FeatureCollection",
            "features": road_features
        }

        # 2. Hazard Layer GeoJSON
        hazard_geojson = {
            "type": "FeatureCollection",
            "features": flood_polygons
        }

        # 3. Bottleneck Choke Points GeoJSON
        choke_features = []
        for ch in node_chokes:
            choke_features.append({
                "type": "Feature",
                "id": ch["node_id"],
                "properties": {
                    "node_id": ch["node_id"],
                    "name": ch["name"],
                    "flood_depth_m": ch["flood_depth_m"],
                    "elevation_m": ch["elevation_m"],
                    "degree_loss_pct": ch["degree_loss_pct"],
                    "in_flow_vehicles": ch["in_flow_vehicles"],
                    "type": ch["type"],
                    "severity": ch["severity"]
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [ch["lon"], ch["lat"]]
                }
            })

        bottlenecks_geojson = {
            "type": "FeatureCollection",
            "features": choke_features
        }

        # 4. Shelters GeoJSON
        shelter_features = []
        for s in city_config.get("shelters", []):
            shelter_features.append({
                "type": "Feature",
                "id": s["id"],
                "properties": {
                    "id": s["id"],
                    "name": s["name"],
                    "capacity": s["capacity"],
                    "elevation_m": s["elevation"],
                    "status": s.get("status", "active")
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [s["lon"], s["lat"]]
                }
            })

        shelters_geojson = {
            "type": "FeatureCollection",
            "features": shelter_features
        }

        # 5. Evacuation Routes GeoJSON
        route_features = []
        for rt in evacuation_routes[:20]:  # Top representative routes
            coords = rt.get("coordinates", [])
            if len(coords) >= 2:
                geojson_coords = [[p[1], p[0]] for p in coords]
                route_features.append({
                    "type": "Feature",
                    "properties": {
                        "origin_name": rt["origin_name"],
                        "destination_name": rt["destination_name"],
                        "demand_vehicles": rt["demand_vehicles"],
                        "estimated_time_min": rt["estimated_time_min"],
                        "is_severely_delayed": rt["is_severely_delayed"]
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": geojson_coords
                    }
                })

        routes_geojson = {
            "type": "FeatureCollection",
            "features": route_features
        }

        # Aggregate Summary Metrics
        total_evac_vehicles = sum(rt["demand_vehicles"] for rt in evacuation_routes)
        avg_travel_time = round(sum(rt["estimated_time_min"] for rt in evacuation_routes) / max(1, len(evacuation_routes)), 1)
        submerged_length_km = round(sum(r["length_m"] for r in scored_roads if r["flood_depth_m"] >= 0.50) / 1000.0, 1)
        total_length_km = round(sum(r["length_m"] for r in scored_roads) / 1000.0, 1)

        payload = {
            "city": {
                "id": city_config["id"],
                "name": city_config["name"],
                "country": city_config["country"],
                "center": city_config["center"],
                "zoom": city_config["zoom"],
                "bbox": city_config["bbox"],
                "description": city_config["description"],
                "water_bodies": city_config.get("water_bodies", [])
            },
            "scenario": {
                "key": scenario_key,
                "name": scenario_meta["name"],
                "rainfall_mm_hr": scenario_meta["rainfall_mm_hr"],
                "surge_m": scenario_meta["surge_m"],
                "duration_hrs": scenario_meta["duration_hrs"],
                "description": scenario_meta["description"]
            },
            "metrics": {
                "total_evac_vehicles": total_evac_vehicles,
                "avg_travel_time_min": avg_travel_time,
                "submerged_road_km": submerged_length_km,
                "total_road_km": total_length_km,
                "submerged_percentage": round((submerged_length_km / max(0.1, total_length_km)) * 100, 1),
                "critical_chokepoints_count": len(node_chokes),
                "tier1_lifelines_count": interventions["critical_lifelines_count"],
                "network_resilience_index": round(max(10.0, 100.0 - (submerged_length_km / max(0.1, total_length_km) * 120.0) - len(node_chokes) * 4.0), 1)
            },
            "interventions": interventions,
            "geo": {
                "roads": roads_geojson,
                "hazard": hazard_geojson,
                "bottlenecks": bottlenecks_geojson,
                "shelters": shelters_geojson,
                "routes": routes_geojson
            }
        }

        return payload

    @classmethod
    def save_payload(cls, payload: Dict[str, Any], filepath: str):
        """Saves JSON payload with formatting."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
