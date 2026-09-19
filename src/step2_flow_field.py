"""
AquaRoute AI - Step 2: Evacuation Flow Field & Dynamic Demand Simulation
Models multi-origin population evacuation demand, capacity-constrained
shelter assignment, and dynamic shortest-path flow accumulation across road links.
"""

import math
import networkx as nx
from typing import Dict, Any, List, Tuple


class FlowFieldSimulator:
    """
    Step 2 Engine: Models evacuation traffic pressure across the road network
    under flooded vs dry conditions.
    """

    def __init__(self, city_config: Dict[str, Any]):
        self.city_config = city_config
        self.shelters = city_config.get("shelters", [])

    def generate_evacuation_demand(self, G: nx.DiGraph) -> List[Dict[str, Any]]:
        """
        Generates population evacuation origin centroids across the city network.
        Nodes with higher flood risk or residential density generate higher demand.
        """
        origins = []
        shelter_coords = [(s["lat"], s["lon"]) for s in self.shelters]

        for node_id, data in G.nodes(data=True):
            lat, lon = data["lat"], data["lon"]
            flood_depth = data.get("flood_depth_m", 0.0)

            # Check if this node is an existing shelter (shelters are destinations, not origins)
            is_shelter = any(
                abs(lat - s_lat) < 0.003 and abs(lon - s_lon) < 0.003
                for s_lat, s_lon in shelter_coords
            )
            if is_shelter:
                continue

            # Base population density around node (vehicles needing evacuation)
            # High flood depth triggers urgent panic evacuation
            if flood_depth > 0.5:
                evacuee_count = 3500
            elif flood_depth > 0.2:
                evacuee_count = 2200
            elif flood_depth > 0.05:
                evacuee_count = 1200
            else:
                evacuee_count = 600  # precautionary / regional transit

            origins.append({
                "node_id": node_id,
                "name": data.get("name", node_id),
                "lat": lat,
                "lon": lon,
                "demand_vehicles": evacuee_count,
                "flood_depth_m": flood_depth
            })

        return origins

    def simulate_evacuation_flows(self, G: nx.DiGraph, origins: List[Dict[str, Any]]) -> Tuple[nx.DiGraph, List[Dict[str, Any]]]:
        """
        Routes evacuees from origins to nearest viable shelters using dynamic travel time.
        Accumulates flow volume F_e on all traversed edges.
        """
        # Initialize edge flows
        for u, v, data in G.edges(data=True):
            data["evacuation_flow_volume"] = 0
            data["flow_routes_count"] = 0

        # Find closest shelter nodes in graph
        shelter_nodes = self._map_shelters_to_nodes(G)

        evacuation_routes = []
        shelter_occupancy = {s["id"]: 0 for s in self.shelters}

        for orig in origins:
            orig_node = orig["node_id"]
            demand = orig["demand_vehicles"]

            # Calculate shortest paths to all active shelters considering flood impedance
            best_shelter_node = None
            best_shelter_meta = None
            shortest_path = None
            min_cost = float("inf")

            for s_node, s_meta in shelter_nodes:
                # Check shelter capacity remaining
                s_id = s_meta["id"]
                if shelter_occupancy[s_id] >= s_meta["capacity"]:
                    continue

                try:
                    # Weight function includes travel time + severe penalty for water depth
                    path = nx.shortest_path(
                        G,
                        source=orig_node,
                        target=s_node,
                        weight=lambda u, v, d: self._edge_impedance(d)
                    )
                    cost = sum(self._edge_impedance(G[u][v]) for u, v in zip(path[:-1], path[1:]))

                    if cost < min_cost:
                        min_cost = cost
                        best_shelter_node = s_node
                        best_shelter_meta = s_meta
                        shortest_path = path
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue

            if shortest_path and best_shelter_meta:
                s_id = best_shelter_meta["id"]
                shelter_occupancy[s_id] += demand

                # Accumulate flows on path edges
                for u, v in zip(shortest_path[:-1], shortest_path[1:]):
                    G[u][v]["evacuation_flow_volume"] += demand
                    G[u][v]["flow_routes_count"] += 1

                # Record route geometry for web rendering
                route_coords = []
                for n in shortest_path:
                    route_coords.append([G.nodes[n]["lat"], G.nodes[n]["lon"]])

                evacuation_routes.append({
                    "origin_id": orig_node,
                    "origin_name": orig["name"],
                    "destination_id": best_shelter_meta["id"],
                    "destination_name": best_shelter_meta["name"],
                    "demand_vehicles": demand,
                    "path_nodes": shortest_path,
                    "coordinates": route_coords,
                    "estimated_time_min": round(min_cost / 60.0, 1),
                    "is_severely_delayed": min_cost > 3600
                })

        return G, evacuation_routes

    def _edge_impedance(self, edge_data: Dict[str, Any]) -> float:
        """
        Custom impedance function: Travel time (sec) scaled heavily by flood depth.
        Submerged edges have near-infinite impedance.
        """
        depth = edge_data.get("flood_depth_m", 0.0)
        t_sec = edge_data.get("travel_time_sec", 60.0)

        if depth >= 0.70:
            return t_sec + 1000000.0  # Impassable
        elif depth >= 0.40:
            return t_sec * 8.0 + 500.0
        elif depth >= 0.20:
            return t_sec * 2.5 + 100.0
        else:
            return t_sec

    def _map_shelters_to_nodes(self, G: nx.DiGraph) -> List[Tuple[str, Dict[str, Any]]]:
        """Maps each configured shelter to the closest network node."""
        shelter_nodes = []
        for s in self.shelters:
            s_lat, s_lon = s["lat"], s["lon"]
            min_dist = float("inf")
            best_node = None
            for n, data in G.nodes(data=True):
                d = self._euclidean_dist(s_lat, s_lon, data["lat"], data["lon"])
                if d < min_dist:
                    min_dist = d
                    best_node = n
            if best_node:
                shelter_nodes.append((best_node, s))
        return shelter_nodes

    @staticmethod
    def _euclidean_dist(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        return math.sqrt((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2)
