"""
AquaRoute AI - Step 1: Hazard Layer & Flood Inundation Simulator
Calculates spatial water depth grid, terrain elevation interaction,
road segment water inundation, vehicle speed degradation, and hazard polygons.
"""

import math
import numpy as np
import networkx as nx
from typing import Dict, Any, List, Tuple
from src.config import CRITICAL_WATER_DEPTHS


class HazardSimulator:
    """
    Step 1 Engine: Simulates hydrological flood inundation across city topography
    and overlays flood depth onto road segments.
    """

    def __init__(self, city_config: Dict[str, Any]):
        self.city_config = city_config
        self.water_bodies = city_config.get("water_bodies", [])
        self.vulnerable_hotspots = city_config.get("vulnerable_hotspots", [])
        self.elevation_baseline = city_config.get("elevation_baseline", 5.0)

    def calculate_point_water_depth(self, lat: float, lon: float, elevation: float,
                                    scenario: Dict[str, Any]) -> float:
        """
        Calculates flood water depth (meters) at a specific coordinate based on:
        - Precipitation rate (mm/hr) & duration
        - Storm surge & astronomical high tide (m)
        - Local elevation vs sea level
        - Proximity to nearest river/creek/ocean body
        - Local topological depressions / vulnerable hotspots
        """
        rainfall_mm_hr = scenario.get("rainfall_mm_hr", 50.0)
        surge_m = scenario.get("surge_m", 0.5)

        # 1. Base pluvial accumulation (rainfall runoff)
        # 100 mm/hr produces approx 0.45m surface water accumulation in urban drainage bottlenecks
        pluvial_base = (rainfall_mm_hr / 100.0) * 0.45

        # 2. Fluvial / Coastal Proximity Effect
        min_water_dist_km = 999.0
        is_ocean = False
        for wb in self.water_bodies:
            for pt in wb["coords"]:
                d_km = self._approx_dist_km(lat, lon, pt[0], pt[1])
                if d_km < min_water_dist_km:
                    min_water_dist_km = d_km
                    is_ocean = (wb["type"] == "ocean")

        # Fluvial surge decaying exponentially with distance from water body
        proximity_factor = math.exp(-min_water_dist_km / 1.5)  # 1.5km decay radius
        coastal_surge_effect = surge_m * proximity_factor if is_ocean else (surge_m * 0.7 * proximity_factor)

        # 3. Elevation & Topographic drainage buffer
        # High elevation drains water; low elevation (< baseline) pools water
        elev_diff = elevation - self.elevation_baseline
        if elev_diff > 0:
            elev_attenuation = math.exp(-elev_diff / 8.0)
        else:
            # Low lying basin effect
            elev_attenuation = 1.0 + abs(elev_diff) * 0.35

        # 4. Known depression hotspots (e.g. subways, low-lying basins)
        hotspot_boost = 0.0
        for spot in self.vulnerable_hotspots:
            d_spot = self._approx_dist_km(lat, lon, spot["lat"], spot["lon"])
            if d_spot < 1.2:
                intensity = (1.0 - d_spot / 1.2) * (spot.get("vuln_weight", 1.2) - 1.0)
                hotspot_boost = max(hotspot_boost, intensity * 0.6)

        # Total combined water depth
        raw_depth = (pluvial_base * elev_attenuation) + (coastal_surge_effect * 0.8) + hotspot_boost

        # If elevation is substantially high (e.g. > 30m), water drains off rapidly
        if elevation > 30.0:
            raw_depth = min(raw_depth, 0.02)
        elif elevation > 15.0:
            raw_depth *= 0.3

        return max(0.0, round(raw_depth, 3))

    def apply_hazard_to_graph(self, G: nx.DiGraph, scenario: Dict[str, Any]) -> nx.DiGraph:
        """
        Calculates flood depth for every node and edge in the network,
        and determines operational speed reduction and passable status.
        """
        # Node flood depths
        for node_id, data in G.nodes(data=True):
            lat, lon = data["lat"], data["lon"]
            elev = data.get("elevation", self.elevation_baseline)
            depth = self.calculate_point_water_depth(lat, lon, elev, scenario)
            data["flood_depth_m"] = depth

        # Edge flood depths (sampled at endpoints and midpoint)
        for u, v, data in G.edges(data=True):
            u_depth = G.nodes[u].get("flood_depth_m", 0.0)
            v_depth = G.nodes[v].get("flood_depth_m", 0.0)

            geom = data.get("geometry", [])
            if geom and len(geom) >= 2:
                mid_lat = (geom[0][0] + geom[-1][0]) / 2.0
                mid_lon = (geom[0][1] + geom[-1][1]) / 2.0
                mid_elev = (G.nodes[u].get("elevation", 5.0) + G.nodes[v].get("elevation", 5.0)) / 2.0
                mid_depth = self.calculate_point_water_depth(mid_lat, mid_lon, mid_elev, scenario)
            else:
                mid_depth = (u_depth + v_depth) / 2.0

            # Bridges have an elevation deck offset of 3.0m unless submerged by catastrophic surge
            if data.get("is_bridge", False):
                edge_depth = max(0.0, mid_depth - 1.8)
            else:
                edge_depth = max(u_depth, v_depth, mid_depth)

            data["flood_depth_m"] = round(edge_depth, 3)

            # Determine Passability & Speed Degradation
            base_speed = data.get("speed_limit", 50.0)
            if edge_depth < CRITICAL_WATER_DEPTHS["dry"]:
                status = "dry"
                speed_factor = 1.0
            elif edge_depth < CRITICAL_WATER_DEPTHS["minor_ponding"]:
                status = "minor_ponding"
                speed_factor = 0.75
            elif edge_depth < CRITICAL_WATER_DEPTHS["moderate_water"]:
                status = "moderate_risk"
                speed_factor = 0.40
            elif edge_depth < CRITICAL_WATER_DEPTHS["severe_flood"]:
                status = "emergency_only"
                speed_factor = 0.15
            else:
                status = "submerged"
                speed_factor = 0.001  # Practically impassable

            data["status"] = status
            data["effective_speed"] = round(base_speed * speed_factor, 1)
            data["is_passable"] = (status != "submerged")

            # Travel time in seconds: length (m) / speed (m/s)
            speed_mps = max(0.1, data["effective_speed"] * (1000.0 / 3600.0))
            data["travel_time_sec"] = round(data["length"] / speed_mps, 1)

        return G

    def generate_flood_polygons(self, scenario: Dict[str, Any], grid_res: int = 18) -> List[Dict[str, Any]]:
        """
        Generates GeoJSON contour polygons / grid cells representing flood depth zones
        for map rendering.
        """
        bbox = self.city_config["bbox"]
        lats = np.linspace(bbox["min_lat"], bbox["max_lat"], grid_res)
        lons = np.linspace(bbox["min_lon"], bbox["max_lon"], grid_res)
        dlat = (lats[1] - lats[0]) / 2.0
        dlon = (lons[1] - lons[0]) / 2.0

        polygons = []
        for lat in lats:
            for lon in lons:
                # Approximate elevation based on hotspot and distance to water
                elev = self._estimate_grid_elevation(lat, lon)
                depth = self.calculate_point_water_depth(lat, lon, elev, scenario)

                if depth >= 0.08:  # Only output noticeable water
                    # Determine severity color category
                    if depth < 0.25:
                        severity = "low"
                        color = "#38bdf8"  # light cyan
                        fill_opacity = 0.35
                    elif depth < 0.60:
                        severity = "medium"
                        color = "#0284c7"  # ocean blue
                        fill_opacity = 0.50
                    elif depth < 1.20:
                        severity = "high"
                        color = "#1e40af"  # deep navy
                        fill_opacity = 0.65
                    else:
                        severity = "critical"
                        color = "#4c1d95"  # deep purple deluge
                        fill_opacity = 0.80

                    cell_bounds = [
                        [lat - dlat, lon - dlon],
                        [lat - dlat, lon + dlon],
                        [lat + dlat, lon + dlon],
                        [lat + dlat, lon - dlon],
                        [lat - dlat, lon - dlon]
                    ]

                    polygons.append({
                        "type": "Feature",
                        "properties": {
                            "depth_m": depth,
                            "severity": severity,
                            "color": color,
                            "opacity": fill_opacity,
                            "elevation_m": round(elev, 1)
                        },
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [[[p[1], p[0]] for p in cell_bounds]]  # GeoJSON [lon, lat]
                        }
                    })

        return polygons

    def _estimate_grid_elevation(self, lat: float, lon: float) -> float:
        """Estimates elevation for a grid cell based on city hotspots and distance to water."""
        elev = self.elevation_baseline
        for spot in self.vulnerable_hotspots:
            d = self._approx_dist_km(lat, lon, spot["lat"], spot["lon"])
            if d < 1.5:
                elev = min(elev, spot.get("elevation", self.elevation_baseline))
        return elev

    @staticmethod
    def _approx_dist_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Fast Euclidean approximation in kilometers."""
        dlat = (lat2 - lat1) * 111.0
        dlon = (lon2 - lon1) * 111.0 * math.cos(math.radians(lat1))
        return math.sqrt(dlat * dlat + dlon * dlon)
