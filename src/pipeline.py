"""
AquaRoute AI - 4-Step Flood Simulation & Road Optimization Pipeline Orchestrator
Executes:
  Step 1: Hazard Layer (Inundation Depth & Terrain DEM)
  Step 2: Flow Field (Evacuation Demand & Dynamic Assignment)
  Step 3: Bottleneck Detection (CVR & Choke Points)
  Step 4: Road Scoring (Criticality Index & Emergency Interventions)
"""

import logging
import os
import sys
from typing import Dict, Any, Optional

from src.config import CITIES_CONFIG
from src.osm_fetcher import NetworkFetcher
from src.step1_hazard import HazardSimulator
from src.step2_flow_field import FlowFieldSimulator
from src.step3_bottlenecks import BottleneckDetector
from src.step4_road_scoring import RoadScoringOptimizer
from src.export_geojson import ScenarioExporter

logger = logging.getLogger("AquaRoute.Pipeline")


class SimulationPipeline:
    """
    End-to-End Orchestrator for AquaRoute 4-Step Simulation Engine.
    """

    def __init__(self, city_id: str):
        if city_id not in CITIES_CONFIG:
            raise ValueError(f"City '{city_id}' not found in configuration. Available: {list(CITIES_CONFIG.keys())}")
        self.city_id = city_id
        self.city_config = CITIES_CONFIG[city_id]
        self.fetcher = NetworkFetcher(cache_dir="data/raw")
        self.hazard_sim = HazardSimulator(self.city_config)
        self.flow_sim = FlowFieldSimulator(self.city_config)
        self.bottleneck_detector = BottleneckDetector()
        self.road_optimizer = RoadScoringOptimizer()

    def run_scenario(self, scenario_key: str = "moderate", force_synthetic: bool = False,
                     output_dir: str = "data/scenarios") -> Dict[str, Any]:
        """
        Runs the complete 4-step simulation for a designated scenario ('mild', 'moderate', 'severe').
        """
        if scenario_key not in self.city_config["scenarios"]:
            raise ValueError(f"Scenario '{scenario_key}' not defined for {self.city_id}. Choose from: {list(self.city_config['scenarios'].keys())}")

        scenario_meta = self.city_config["scenarios"][scenario_key]
        logger.info(f"=== Starting 4-Step Simulation: {self.city_config['name']} [{scenario_meta['name']}] ===")

        # Step 0: Network Graph Construction
        logger.info("[Step 0] Constructing road network graph...")
        G = self.fetcher.get_or_build_graph(self.city_config, force_synthetic=force_synthetic)
        logger.info(f"Graph ready: {G.number_of_nodes()} nodes, {G.number_of_edges()} directional edges.")

        # Step 1: Hazard Layer Inundation & Road Flood Depth
        logger.info("[Step 1/4] Simulating Hazard Layer (Hydrology & Topography)...")
        G = self.hazard_sim.apply_hazard_to_graph(G, scenario_meta)
        flood_polygons = self.hazard_sim.generate_flood_polygons(scenario_meta, grid_res=20)
        logger.info(f"Hazard generated: {len(flood_polygons)} inundated grid sectors.")

        # Step 2: Evacuation Flow Field & Dynamic Demand
        logger.info("[Step 2/4] Simulating Evacuation Demand & Flow Field...")
        origins = self.flow_sim.generate_evacuation_demand(G)
        G, evacuation_routes = self.flow_sim.simulate_evacuation_flows(G, origins)
        logger.info(f"Flow field computed: {len(evacuation_routes)} evacuation corridors assigned.")

        # Step 3: Bottleneck Detection & Choke Points
        logger.info("[Step 3/4] Detecting Bottlenecks & Cutoff Risks...")
        G, edge_bottlenecks, node_chokes = self.bottleneck_detector.analyze_bottlenecks(G)
        logger.info(f"Bottlenecks isolated: {len(edge_bottlenecks)} saturated links, {len(node_chokes)} choke nodes.")

        # Step 4: Road Criticality Scoring & Interventions
        logger.info("[Step 4/4] Computing Multi-Factor Road Criticality Scores...")
        G, scored_roads = self.road_optimizer.compute_road_criticality(G)
        interventions = self.road_optimizer.generate_intervention_plan(scored_roads, node_chokes)
        logger.info(f"Scoring complete: {interventions['critical_lifelines_count']} Tier-1 lifelines prioritized.")

        # Serialization
        payload = ScenarioExporter.build_web_scenario_payload(
            city_config=self.city_config,
            scenario_key=scenario_key,
            scenario_meta=scenario_meta,
            G=G,
            flood_polygons=flood_polygons,
            evacuation_routes=evacuation_routes,
            edge_bottlenecks=edge_bottlenecks,
            node_chokes=node_chokes,
            scored_roads=scored_roads,
            interventions=interventions
        )

        out_filename = f"{self.city_id}_{scenario_key}.json"
        out_filepath = os.path.join(output_dir, out_filename)
        ScenarioExporter.save_payload(payload, out_filepath)
        logger.info(f"Saved scenario package to {out_filepath}")

        # Also copy/symlink to web/data for direct client loading
        web_data_dir = os.path.join("web", "data")
        os.makedirs(web_data_dir, exist_ok=True)
        web_filepath = os.path.join(web_data_dir, out_filename)
        ScenarioExporter.save_payload(payload, web_filepath)

        return payload


def run_all():
    """Generates all 9 pre-computed scenarios across all 3 cities."""
    cities = ["mumbai", "jakarta", "houston"]
    scenarios = ["mild", "moderate", "severe"]

    for city in cities:
        sim = SimulationPipeline(city)
        for sc in scenarios:
            sim.run_scenario(sc, force_synthetic=True)

    print("\n[SUCCESS] All 9 precomputed scenarios successfully generated!")


if __name__ == "__main__":
    if len(sys.argv) > 2:
        city_arg = sys.argv[1]
        sc_arg = sys.argv[2]
        pipeline = SimulationPipeline(city_arg)
        pipeline.run_scenario(sc_arg, force_synthetic=True)
    else:
        run_all()
