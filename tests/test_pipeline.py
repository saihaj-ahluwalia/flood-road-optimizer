"""
AquaRoute AI - Automated Test Suite
Validates the 4-Step Flood Simulation & Road Optimization Pipeline:
  1. Hazard Inundation calculation
  2. Flow Field & Shortest-path routing
  3. Bottleneck detection (CVR & Choke points)
  4. Multi-Criteria Road Criticality Scoring (RCS)
  5. GeoJSON payload integrity across all 3 cities & scenarios
"""

import unittest
import os
import json
import networkx as nx

from src.config import CITIES_CONFIG, CRITICAL_WATER_DEPTHS, SCORING_WEIGHTS
from src.osm_fetcher import NetworkFetcher, haversine_distance
from src.step1_hazard import HazardSimulator
from src.step2_flow_field import FlowFieldSimulator
from src.step3_bottlenecks import BottleneckDetector
from src.step4_road_scoring import RoadScoringOptimizer
from src.pipeline import SimulationPipeline


class TestAquaRoutePipeline(unittest.TestCase):

    def setUp(self):
        self.cities = ["mumbai", "jakarta", "houston"]
        self.fetcher = NetworkFetcher(cache_dir="data/raw")

    def test_haversine_formula(self):
        """Verify Haversine distance accuracy."""
        # Mumbai CST to Dadar ~ 8.5 km
        dist = haversine_distance(18.9400, 72.8350, 19.0180, 72.8430)
        self.assertTrue(8000 < dist < 9500, f"Distance {dist} out of expected range")

    def test_city_network_construction(self):
        """Verify graph construction for all 3 cities."""
        for city_id in self.cities:
            config = CITIES_CONFIG[city_id]
            G = self.fetcher.get_or_build_graph(config, force_synthetic=True)
            self.assertGreater(G.number_of_nodes(), 15, f"{city_id} has too few nodes")
            self.assertGreater(G.number_of_edges(), 30, f"{city_id} has too few edges")

            # Verify node coordinates exist
            for n, d in G.nodes(data=True):
                self.assertIn("lat", d)
                self.assertIn("lon", d)
                self.assertIn("elevation", d)

            # Verify edge attributes
            for u, v, d in G.edges(data=True):
                self.assertIn("length", d)
                self.assertIn("capacity", d)
                self.assertIn("speed_limit", d)

    def test_step1_hazard_simulation(self):
        """Verify flood inundation and speed degradation."""
        for city_id in self.cities:
            config = CITIES_CONFIG[city_id]
            G = self.fetcher.get_or_build_graph(config, force_synthetic=True)
            hazard_sim = HazardSimulator(config)

            scenario = config["scenarios"]["severe"]
            G = hazard_sim.apply_hazard_to_graph(G, scenario)

            for u, v, d in G.edges(data=True):
                self.assertIn("flood_depth_m", d)
                self.assertGreaterEqual(d["flood_depth_m"], 0.0)
                self.assertIn("effective_speed", d)
                self.assertIn("status", d)

            # Check flood polygons
            polys = hazard_sim.generate_flood_polygons(scenario, grid_res=10)
            self.assertGreater(len(polys), 0)

    def test_step2_flow_field(self):
        """Verify dynamic evacuation routing and flow accumulation."""
        for city_id in self.cities:
            config = CITIES_CONFIG[city_id]
            G = self.fetcher.get_or_build_graph(config, force_synthetic=True)
            hazard_sim = HazardSimulator(config)
            flow_sim = FlowFieldSimulator(config)

            G = hazard_sim.apply_hazard_to_graph(G, config["scenarios"]["moderate"])
            origins = flow_sim.generate_evacuation_demand(G)
            self.assertGreater(len(origins), 5)

            G, routes = flow_sim.simulate_evacuation_flows(G, origins)
            self.assertGreater(len(routes), 0)

            total_flow = sum(d.get("evacuation_flow_volume", 0) for u, v, d in G.edges(data=True))
            self.assertGreater(total_flow, 0)

    def test_step3_bottlenecks(self):
        """Verify Capacity-to-Volume Ratio and choke point identification."""
        for city_id in self.cities:
            config = CITIES_CONFIG[city_id]
            G = self.fetcher.get_or_build_graph(config, force_synthetic=True)
            hazard_sim = HazardSimulator(config)
            flow_sim = FlowFieldSimulator(config)
            bottleneck_detector = BottleneckDetector()

            G = hazard_sim.apply_hazard_to_graph(G, config["scenarios"]["severe"])
            origins = flow_sim.generate_evacuation_demand(G)
            G, routes = flow_sim.simulate_evacuation_flows(G, origins)

            G, edge_bnecks, node_chokes = bottleneck_detector.analyze_bottlenecks(G)
            self.assertIsInstance(edge_bnecks, list)
            self.assertIsInstance(node_chokes, list)

            for b in edge_bnecks:
                self.assertIn("cvr", b)
                self.assertIn("severity", b)

    def test_step4_road_scoring(self):
        """Verify Road Criticality Score (RCS) calculation and prioritization tiers."""
        for city_id in self.cities:
            config = CITIES_CONFIG[city_id]
            G = self.fetcher.get_or_build_graph(config, force_synthetic=True)
            hazard_sim = HazardSimulator(config)
            flow_sim = FlowFieldSimulator(config)
            bottleneck_detector = BottleneckDetector()
            optimizer = RoadScoringOptimizer()

            G = hazard_sim.apply_hazard_to_graph(G, config["scenarios"]["moderate"])
            origins = flow_sim.generate_evacuation_demand(G)
            G, routes = flow_sim.simulate_evacuation_flows(G, origins)
            G, edge_bnecks, node_chokes = bottleneck_detector.analyze_bottlenecks(G)

            G, scored = optimizer.compute_road_criticality(G)
            self.assertEqual(len(scored), G.number_of_edges())

            # Verify scores are bounded between 0 and 100
            for r in scored:
                self.assertTrue(0.0 <= r["criticality_score"] <= 100.0)
                self.assertIn("tier", r)
                self.assertIn("recommended_action", r)

            plan = optimizer.generate_intervention_plan(scored, node_chokes)
            self.assertIn("priority_interventions", plan)

    def test_end_to_end_precomputed_json_files(self):
        """Verify that all 9 pre-computed JSON files exist, load properly, and have valid GeoJSON."""
        scenarios = ["mild", "moderate", "severe"]
        for city_id in self.cities:
            for sc in scenarios:
                path = os.path.join("data", "scenarios", f"{city_id}_{sc}.json")
                self.assertTrue(os.path.exists(path), f"Missing scenario file: {path}")

                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.assertIn("city", data)
                self.assertIn("scenario", data)
                self.assertIn("metrics", data)
                self.assertIn("interventions", data)
                self.assertIn("geo", data)

                # Validate GeoJSON FeatureCollections
                for key in ["roads", "hazard", "bottlenecks", "shelters", "routes"]:
                    self.assertIn(key, data["geo"])
                    self.assertEqual(data["geo"][key]["type"], "FeatureCollection")
                    self.assertGreater(len(data["geo"][key]["features"]), 0)


if __name__ == "__main__":
    unittest.main()
