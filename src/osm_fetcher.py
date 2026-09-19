"""
AquaRoute AI - OpenStreetMap Network Fetcher & Graph Constructor
Handles live Overpass API queries and provides deterministic, high-fidelity
topological road graphs matching actual city geography for Mumbai, Jakarta, and Houston.
"""

import json
import logging
import math
import os
import requests
import networkx as nx
from typing import Dict, Any, Tuple, Optional, List

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AquaRoute.OSM")


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes the great-circle distance between two GPS coordinates in meters.
    """
    R = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class NetworkFetcher:
    """
    Fetches or generates structured NetworkX road graphs with full geographic coordinates,
    capacity metrics, speed limits, and road hierarchy attributes.
    """

    OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    def __init__(self, cache_dir: str = "data/raw"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def fetch_from_overpass(self, city_id: str, bbox: Dict[str, float], timeout: int = 25) -> Optional[nx.DiGraph]:
        """
        Attempts to query the live Overpass API for driveable highways within the bounding box.
        """
        cache_file = os.path.join(self.cache_dir, f"{city_id}_osm_raw.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(f"Loaded cached Overpass data for {city_id}")
                return self._parse_overpass_json(data)
            except Exception as e:
                logger.warning(f"Failed to read cache {cache_file}: {e}")

        query = f"""
        [out:json][timeout:{timeout}];
        (
          way["highway"~"motorway|trunk|primary|secondary|tertiary|bridge"]
            ({bbox['min_lat']},{bbox['min_lon']},{bbox['max_lat']},{bbox['max_lon']});
        );
        out body;
        >;
        out skel qt;
        """
        try:
            logger.info(f"Querying Overpass API for {city_id}...")
            response = requests.post(self.OVERPASS_URL, data={"data": query}, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                return self._parse_overpass_json(data)
            else:
                logger.warning(f"Overpass returned HTTP {response.status_code}. Falling back to topology generator.")
                return None
        except Exception as e:
            logger.warning(f"Overpass fetch error ({e}). Using robust geometric graph builder.")
            return None

    def _parse_overpass_json(self, data: Dict[str, Any]) -> nx.DiGraph:
        """Parses raw Overpass JSON into a NetworkX directed graph."""
        G = nx.DiGraph()
        nodes = {}
        for el in data.get("elements", []):
            if el["type"] == "node":
                nodes[el["id"]] = (el["lat"], el["lon"])
                G.add_node(el["id"], lat=el["lat"], lon=el["lon"], elevation=5.0)

        for el in data.get("elements", []):
            if el["type"] == "way" and "nodes" in el:
                way_nodes = el["nodes"]
                tags = el.get("tags", {})
                highway = tags.get("highway", "primary")
                name = tags.get("name", "Unnamed Road")
                is_bridge = "bridge" in tags or tags.get("bridge") == "yes"

                speed = 60 if highway in ["motorway", "trunk"] else 40
                capacity = 3000 if highway in ["motorway", "trunk"] else 1800

                for u, v in zip(way_nodes[:-1], way_nodes[1:]):
                    if u in nodes and v in nodes:
                        dist = haversine_distance(nodes[u][0], nodes[u][1], nodes[v][0], nodes[v][1])
                        edge_id = f"{u}_{v}"
                        G.add_edge(
                            u, v,
                            id=edge_id,
                            name=name,
                            highway=highway,
                            length=max(10.0, dist),
                            speed_limit=speed,
                            capacity=capacity,
                            is_bridge=is_bridge,
                            geometry=[[nodes[u][0], nodes[u][1]], [nodes[v][0], nodes[v][1]]]
                        )
                        # Assume two-way if not oneway
                        if tags.get("oneway") != "yes":
                            rev_id = f"{v}_{u}"
                            G.add_edge(
                                v, u,
                                id=rev_id,
                                name=name,
                                highway=highway,
                                length=max(10.0, dist),
                                speed_limit=speed,
                                capacity=capacity,
                                is_bridge=is_bridge,
                                geometry=[[nodes[v][0], nodes[v][1]], [nodes[u][0], nodes[u][1]]]
                            )
        return G

    def get_or_build_graph(self, city_config: Dict[str, Any], force_synthetic: bool = False) -> nx.DiGraph:
        """
        Returns a rich road network graph for the given city.
        If live fetch is not available or force_synthetic is True, builds a geographically
        precise network based on actual city topology.
        """
        city_id = city_config["id"]
        if not force_synthetic:
            g = self.fetch_from_overpass(city_id, city_config["bbox"])
            if g is not None and g.number_of_nodes() > 20 and g.number_of_edges() > 30:
                logger.info(f"Successfully constructed graph for {city_id} from OSM data ({g.number_of_nodes()} nodes, {g.number_of_edges()} edges)")
                return g

        logger.info(f"Generating high-precision geometric road graph for {city_id}...")
        if city_id == "mumbai":
            return self._build_mumbai_network()
        elif city_id == "jakarta":
            return self._build_jakarta_network()
        elif city_id == "houston":
            return self._build_houston_network()
        else:
            raise ValueError(f"Unknown city ID: {city_id}")

    # =========================================================================
    # High-Fidelity City Topology Constructors (Accurate to Real Landmarks)
    # =========================================================================

    def _build_mumbai_network(self) -> nx.DiGraph:
        """Constructs Mumbai's arterial road spine."""
        G = nx.DiGraph()

        # Key Landmarks and Intersections in Mumbai [lat, lon, approx_elev_m]
        nodes_data = {
            "MUM_COLABA": (18.9150, 72.8250, 5.0, "Colaba Southern Terminal"),
            "MUM_FORT": (18.9350, 72.8350, 6.0, "Fort Heritage & CST Junction"),
            "MUM_MARINEDRIVE": (18.9440, 72.8230, 4.5, "Marine Drive Promenade"),
            "MUM_WORLI": (19.0180, 72.8180, 5.5, "Worli Seaface Junction"),
            "MUM_DADAR_TT": (19.0180, 72.8430, 3.2, "Dadar TT / Hindmata Lowland"),
            "MUM_SHIVAJIPARK": (19.0270, 72.8380, 9.5, "Shivaji Park Safe Zone"),
            "MUM_MAHIM": (19.0400, 72.8420, 4.0, "Mahim Creek Interchange"),
            "MUM_BANDRA_WEST": (19.0550, 72.8300, 7.0, "Bandra Linking Rd Junction"),
            "MUM_BANDRA_EAST": (19.0600, 72.8520, 6.0, "Bandra East Kalanagar"),
            "MUM_BKC_CORE": (19.0650, 72.8690, 12.0, "BKC MMRDA Central Hub"),
            "MUM_DHARAVI": (19.0440, 72.8550, 3.9, "Dharavi Junction"),
            "MUM_SION": (19.0380, 72.8600, 3.8, "Sion Circle & Highway Split"),
            "MUM_KURLA_WEST": (19.0680, 72.8780, 4.1, "Kurla West Mithi Basin"),
            "MUM_KURLA_EAST": (19.0660, 72.8890, 6.5, "Kurla East SCLR Hub"),
            "MUM_GHATKOPAR": (19.0860, 72.9080, 8.0, "Ghatkopar EEH Junction"),
            "MUM_SANTA_CRUZ": (19.0820, 72.8410, 5.0, "Santacruz SV Road"),
            "MUM_AIRPORT_WEH": (19.0950, 72.8550, 8.0, "CSMIA Airport WEH Flyover"),
            "MUM_MILAN_SUBWAY": (19.0890, 72.8450, 2.5, "Milan Subway Depression"),
            "MUM_ANDHERI_WEST": (19.1190, 72.8460, 4.5, "Andheri West SV Rd"),
            "MUM_ANDHERI_EAST": (19.1150, 72.8690, 11.0, "Andheri East Metro Hub"),
            "MUM_JVLR_WEST": (19.1350, 72.8600, 10.0, "JVLR Western End"),
            "MUM_POWAI_IIT": (19.1330, 72.9150, 45.0, "IIT Bombay Powai Plateau"),
            "MUM_VIKHROLI_EEH": (19.1100, 72.9300, 9.0, "Vikhroli EEH Corridor"),
            "MUM_CHEMBUR": (19.0520, 72.8980, 7.5, "Chembur Monorail Hub"),
            "MUM_SOMAIYA": (19.0730, 72.8990, 18.0, "Somaiya Vidyavihar Safe Hub"),
            "MUM_SP_HIGHWAY": (19.0400, 72.9150, 6.0, "Sion-Panvel Highway Split"),
            "MUM_ANDHERI_SPORTS": (19.1310, 72.8350, 14.0, "Andheri Sports Complex Relief"),
            "MUM_GOREGAON_WEH": (19.1550, 72.8580, 12.0, "Goregaon Hub WEH"),
            "MUM_BWSL_NORTH": (19.0450, 72.8180, 8.0, "Bandra-Worli Sea Link Toll")
        }

        for nid, (lat, lon, elev, name) in nodes_data.items():
            G.add_node(nid, lat=lat, lon=lon, elevation=elev, name=name)

        # Arterial Segments: (u, v, name, highway, speed, capacity, is_bridge)
        edges_data = [
            ("MUM_COLABA", "MUM_FORT", "Colaba Causeway", "primary", 40, 2200, False),
            ("MUM_FORT", "MUM_MARINEDRIVE", "Churchgate Connector", "primary", 50, 2500, False),
            ("MUM_MARINEDRIVE", "MUM_WORLI", "Marine Drive & Haji Ali Corridor", "trunk", 60, 3200, False),
            ("MUM_FORT", "MUM_DADAR_TT", "Dr. B.R. Ambedkar Road", "primary", 45, 2600, False),
            ("MUM_WORLI", "MUM_BWSL_NORTH", "Bandra-Worli Sea Link", "motorway", 80, 4500, True),
            ("MUM_BWSL_NORTH", "MUM_BANDRA_WEST", "BWSL Bandra Promenade", "motorway", 70, 4000, True),
            ("MUM_WORLI", "MUM_SHIVAJIPARK", "Dr. Annie Besant Road", "primary", 45, 2200, False),
            ("MUM_SHIVAJIPARK", "MUM_DADAR_TT", "Gokhale Road Connector", "secondary", 35, 1800, False),
            ("MUM_DADAR_TT", "MUM_SION", "Lalbaug Flyover - Sion Corridor", "trunk", 55, 3000, False),
            ("MUM_SHIVAJIPARK", "MUM_MAHIM", "Lady Jamshedji Road", "primary", 40, 2000, False),
            ("MUM_MAHIM", "MUM_BANDRA_WEST", "Mahim Causeway Bridge", "trunk", 50, 3200, True),
            ("MUM_MAHIM", "MUM_DHARAVI", "Mahim-Dharavi Link", "secondary", 35, 1600, False),
            ("MUM_DHARAVI", "MUM_SION", "Sion-Dharavi Connector", "secondary", 35, 1700, False),
            ("MUM_DHARAVI", "MUM_BANDRA_EAST", "Kalanagar Junction Flyover", "trunk", 50, 2800, False),
            ("MUM_BANDRA_WEST", "MUM_BANDRA_EAST", "Bandra Station Flyover", "secondary", 35, 1800, True),
            ("MUM_BANDRA_EAST", "MUM_BKC_CORE", "BKC Central Avenue", "primary", 50, 3200, False),
            ("MUM_BANDRA_EAST", "MUM_SANTA_CRUZ", "Western Express Highway - S1", "motorway", 70, 4200, False),
            ("MUM_SANTA_CRUZ", "MUM_MILAN_SUBWAY", "SV Road Santacruz Cross", "secondary", 35, 1500, False),
            ("MUM_MILAN_SUBWAY", "MUM_AIRPORT_WEH", "Milan Subway Underpass", "secondary", 30, 1400, False),
            ("MUM_SANTA_CRUZ", "MUM_AIRPORT_WEH", "WEH Domestic Flyover", "motorway", 70, 4200, False),
            ("MUM_BKC_CORE", "MUM_KURLA_WEST", "Mithi River BKC-Kurla Bridge", "primary", 45, 2500, True),
            ("MUM_SION", "MUM_KURLA_WEST", "LBS Marg Sion-Kurla Stretch", "primary", 40, 2000, False),
            ("MUM_SION", "MUM_CHEMBUR", "Eastern Express Highway - S1", "motorway", 75, 4200, False),
            ("MUM_CHEMBUR", "MUM_SP_HIGHWAY", "Sion-Panvel Expressway", "motorway", 80, 4500, False),
            ("MUM_CHEMBUR", "MUM_SOMAIYA", "Vidyavihar Link", "secondary", 40, 1800, False),
            ("MUM_KURLA_WEST", "MUM_KURLA_EAST", "Kurla Level Crossing Flyover", "secondary", 35, 1700, True),
            ("MUM_KURLA_EAST", "MUM_SOMAIYA", "SCLR East Connector", "primary", 50, 2800, False),
            ("MUM_BKC_CORE", "MUM_KURLA_EAST", "Santacruz-Chembur Link Road (SCLR)", "trunk", 60, 3500, True),
            ("MUM_SOMAIYA", "MUM_GHATKOPAR", "Eastern Express Highway - S2", "motorway", 75, 4200, False),
            ("MUM_AIRPORT_WEH", "MUM_ANDHERI_EAST", "WEH Sahar Elevated Corridor", "motorway", 70, 4000, False),
            ("MUM_ANDHERI_WEST", "MUM_ANDHERI_EAST", "Andheri Subway & Station Bridge", "secondary", 30, 1600, True),
            ("MUM_ANDHERI_WEST", "MUM_ANDHERI_SPORTS", "SV Road Versova Link", "primary", 40, 2200, False),
            ("MUM_ANDHERI_EAST", "MUM_KURLA_WEST", "Andheri-Kurla Road (Saki Naka)", "primary", 40, 2200, False),
            ("MUM_ANDHERI_EAST", "MUM_JVLR_WEST", "WEH Andheri-JVLR Stretch", "motorway", 70, 4200, False),
            ("MUM_JVLR_WEST", "MUM_POWAI_IIT", "Jogeshwari-Vikhroli Link Road (JVLR)", "trunk", 60, 3600, False),
            ("MUM_POWAI_IIT", "MUM_VIKHROLI_EEH", "JVLR Eastern Descent", "trunk", 60, 3600, False),
            ("MUM_GHATKOPAR", "MUM_VIKHROLI_EEH", "EEH Ghatkopar-Vikhroli Stretch", "motorway", 75, 4200, False),
            ("MUM_JVLR_WEST", "MUM_GOREGAON_WEH", "WEH Goregaon North Corridor", "motorway", 75, 4200, False)
        ]

        self._add_bidirectional_edges(G, edges_data)
        return G

    def _build_jakarta_network(self) -> nx.DiGraph:
        """Constructs Jakarta's arterial ring and radial network."""
        G = nx.DiGraph()

        nodes_data = {
            "JKT_PLUIT": (-6.1250, 106.7950, -1.8, "Pluit Lowland Sea-Gate"),
            "JKT_MUARABARU": (-6.1150, 106.8100, -2.1, "Muara Baru Subsidence Polder"),
            "JKT_ANCOL": (-6.1260, 106.8420, -0.5, "Ancol Coastal Gate"),
            "JKT_TANJUNGPRIOK": (-6.1100, 106.8850, 1.5, "Tanjung Priok Port Hub"),
            "JKT_KOTA": (-6.1380, 106.8150, 2.0, "Kota Tua Heritage Station"),
            "JKT_GROGOL": (-6.1680, 106.7890, 1.5, "Grogol Trisakti Junction"),
            "JKT_MONAS": (-6.1754, 106.8272, 15.0, "Monas National Monument Hub"),
            "JKT_KELAPAGADING": (-6.1580, 106.9050, 0.8, "Kelapa Gading Lowland"),
            "JKT_THAMRIN": (-6.1920, 106.8230, 8.5, "Bundaran HI Thamrin"),
            "JKT_SENAYAN_GBK": (-6.2185, 106.8018, 16.5, "GBK Stadium Mega Shelter"),
            "JKT_SUDIRMAN": (-6.2100, 106.8200, 11.0, "Sudirman CBD Corridor"),
            "JKT_KUNINGAN": (-6.2250, 106.8300, 12.0, "Rasuna Said Kuningan"),
            "JKT_KAMPUNGMELAYU": (-6.2280, 106.8650, 2.2, "Kampung Melayu Ciliwung Basin"),
            "JKT_VELODROME": (-6.1920, 106.8910, 14.0, "Jakarta International Velodrome"),
            "JKT_SLIPI": (-6.1980, 106.7980, 7.5, "Slipi Flyover Toll Gate"),
            "JKT_GATSU": (-6.2350, 106.8180, 10.0, "Jl. Gatot Subroto Corridor"),
            "JKT_CAWANG": (-6.2480, 106.8720, 8.0, "Cawang Interchange Hub"),
            "JKT_BIDARACINA": (-6.2410, 106.8680, 3.0, "Bidara Cina Fluvial Zone"),
            "JKT_HALIM": (-6.2650, 106.8900, 28.0, "Halim Relief Depot"),
            "JKT_BLOKM": (-6.2440, 106.7980, 18.0, "Blok M Terminal Safe Ground"),
            "JKT_SIMATUPANG": (-6.2950, 106.8350, 24.0, "TB Simatupang Outer Ring"),
            "JKT_DEPOK_UI": (-6.3600, 106.8300, 55.0, "Universitas Indonesia Campus")
        }

        for nid, (lat, lon, elev, name) in nodes_data.items():
            G.add_node(nid, lat=lat, lon=lon, elevation=elev, name=name)

        edges_data = [
            ("JKT_PLUIT", "JKT_MUARABARU", "Jl. Pluit Raya Coastal", "primary", 40, 2000, False),
            ("JKT_PLUIT", "JKT_GROGOL", "Tol Pluit-Grogol (Inner Ring)", "motorway", 70, 4200, True),
            ("JKT_MUARABARU", "JKT_ANCOL", "Jl. Lodan Raya", "primary", 35, 1800, False),
            ("JKT_ANCOL", "JKT_TANJUNGPRIOK", "Tol Pelabuhan Highway", "motorway", 75, 4500, True),
            ("JKT_PLUIT", "JKT_KOTA", "Jl. Jembatan Tiga", "secondary", 35, 1600, True),
            ("JKT_KOTA", "JKT_MONAS", "Jl. Gajah Mada / Hayam Wuruk", "primary", 45, 2500, False),
            ("JKT_GROGOL", "JKT_SLIPI", "Jl. S. Parman Corridor", "motorway", 65, 4000, False),
            ("JKT_GROGOL", "JKT_MONAS", "Jl. Kyai Tapa - Cideng Link", "primary", 40, 2200, False),
            ("JKT_ANCOL", "JKT_MONAS", "Jl. Gunung Sahari", "primary", 45, 2500, False),
            ("JKT_ANCOL", "JKT_KELAPAGADING", "Jl. Danau Sunter Utara", "primary", 45, 2200, False),
            ("JKT_KELAPAGADING", "JKT_VELODROME", "Jl. Perintis Kemerdekaan", "trunk", 50, 3000, False),
            ("JKT_MONAS", "JKT_THAMRIN", "Jl. M.H. Thamrin Boulevard", "trunk", 50, 3500, False),
            ("JKT_THAMRIN", "JKT_SUDIRMAN", "Jl. Jend. Sudirman", "trunk", 55, 3800, False),
            ("JKT_SLIPI", "JKT_SENAYAN_GBK", "Jl. Gatot Subroto West", "motorway", 70, 4200, False),
            ("JKT_SUDIRMAN", "JKT_SENAYAN_GBK", "Jl. Jend. Sudirman GBK Entry", "primary", 50, 3000, False),
            ("JKT_SUDIRMAN", "JKT_KUNINGAN", "Jl. Prof. Dr. Satrio (Casablanca)", "trunk", 50, 3000, True),
            ("JKT_KUNINGAN", "JKT_KAMPUNGMELAYU", "Jl. KH Abdullah Syafei (Ciliwung Bridge)", "primary", 40, 2000, True),
            ("JKT_KAMPUNGMELAYU", "JKT_BIDARACINA", "Jl. Otto Iskandardinata", "primary", 40, 2000, False),
            ("JKT_KAMPUNGMELAYU", "JKT_VELODROME", "Jl. Jend. Ahmad Yani (East Ring)", "motorway", 70, 4000, False),
            ("JKT_SENAYAN_GBK", "JKT_BLOKM", "Jl. Sisingamangaraja", "primary", 45, 2400, False),
            ("JKT_SENAYAN_GBK", "JKT_GATSU", "Jl. Gatot Subroto Semanggi Interchange", "motorway", 70, 4500, True),
            ("JKT_GATSU", "JKT_CAWANG", "Tol Dalam Kota (Inner Ring East)", "motorway", 70, 4500, False),
            ("JKT_BIDARACINA", "JKT_CAWANG", "Jl. MT Haryono Corridor", "trunk", 50, 3200, False),
            ("JKT_CAWANG", "JKT_HALIM", "Jl. Halim Perdanakusuma", "primary", 50, 2800, False),
            ("JKT_CAWANG", "JKT_SIMATUPANG", "Tol Jagorawi - JORR Split", "motorway", 80, 4500, False),
            ("JKT_BLOKM", "JKT_SIMATUPANG", "Jl. Fatmawati Corridor", "primary", 45, 2400, False),
            ("JKT_SIMATUPANG", "JKT_DEPOK_UI", "Jl. Margonda Raya Extension", "trunk", 60, 3500, False)
        ]

        self._add_bidirectional_edges(G, edges_data)
        return G

    def _build_houston_network(self) -> nx.DiGraph:
        """Constructs Houston's grid, loop, and radial freeway system."""
        G = nx.DiGraph()

        nodes_data = {
            "HOU_ADDICKS": (29.7880, -95.5100, 13.5, "Addicks Reservoir Spillway"),
            "HOU_I10_WEST": (29.7850, -95.4600, 12.0, "I-10 Katy Freeway / Memorial"),
            "HOU_MEMORIAL_PARK": (29.7650, -95.4300, 11.0, "Memorial Park Bayou Green"),
            "HOU_I10_WHITEOAK": (29.7750, -95.3720, 9.2, "I-10 & White Oak Bayou Interchange"),
            "HOU_NORTH_I45": (29.8200, -95.3800, 15.0, "I-45 North Main Corridor"),
            "HOU_I45_UNDERPASS": (29.7820, -95.3650, 9.8, "I-45 North Main Underpass"),
            "HOU_DOWNTOWN_CORE": (29.7580, -95.3650, 14.0, "Downtown Houston Central"),
            "HOU_GRB_SHELTER": (29.7522, -95.3582, 16.0, "GRB Convention Center Shelter"),
            "HOU_TOYOTA_CENTER": (29.7508, -95.3621, 17.5, "Toyota Center Relief Complex"),
            "HOU_BUFFALO_BAYOU_PK": (29.7610, -95.3750, 8.5, "Allen Parkway Buffalo Bayou"),
            "HOU_LOOP610_NORTH": (29.8050, -95.4100, 16.0, "Loop 610 North Freeway Cross"),
            "HOU_LOOP610_WEST": (29.7400, -95.4600, 15.0, "Loop 610 West Galleria Hub"),
            "HOU_WESTHEIMER": (29.7420, -95.4100, 14.0, "Westheimer Commercial Corridor"),
            "HOU_MED_CENTER": (29.7080, -95.3980, 15.5, "Texas Medical Center Hub"),
            "HOU_RICE_UNIV": (29.7174, -95.4018, 22.0, "Rice University Safe Campus"),
            "HOU_UH_CAMPUS": (29.7199, -95.3422, 19.5, "Univ of Houston Relief Zone"),
            "HOU_MEYERLAND": (29.6880, -95.4600, 11.0, "Meyerland Brays Bayou Basin"),
            "HOU_NRG_PARK": (29.6847, -95.4107, 21.0, "NRG Multi-Disaster Mega Shelter"),
            "HOU_LOOP610_SOUTH": (29.6750, -95.3700, 14.0, "Loop 610 South Fwy Intersect"),
            "HOU_EAST_END": (29.7350, -95.3050, 7.8, "East End Ship Channel Fringe"),
            "HOU_I10_EAST": (29.7680, -95.2900, 8.5, "I-10 East Freeway Bridge")
        }

        for nid, (lat, lon, elev, name) in nodes_data.items():
            G.add_node(nid, lat=lat, lon=lon, elevation=elev, name=name)

        edges_data = [
            ("HOU_ADDICKS", "HOU_I10_WEST", "I-10 Katy Freeway West", "motorway", 85, 5500, False),
            ("HOU_I10_WEST", "HOU_LOOP610_WEST", "I-10 / Loop 610 West Interchange", "motorway", 85, 5500, True),
            ("HOU_I10_WEST", "HOU_MEMORIAL_PARK", "Memorial Drive Arterial", "primary", 55, 2800, False),
            ("HOU_MEMORIAL_PARK", "HOU_BUFFALO_BAYOU_PK", "Allen Parkway Bayou Drive", "primary", 50, 2400, False),
            ("HOU_LOOP610_WEST", "HOU_WESTHEIMER", "Westheimer Galleria Spine", "primary", 50, 3000, False),
            ("HOU_LOOP610_WEST", "HOU_MEYERLAND", "Loop 610 West - Meyerland", "motorway", 80, 5000, False),
            ("HOU_MEYERLAND", "HOU_NRG_PARK", "S. Braeswood Blvd (Brays Bayou)", "primary", 45, 2200, True),
            ("HOU_NORTH_I45", "HOU_LOOP610_NORTH", "I-45 North Freeway Segment 1", "motorway", 80, 5200, False),
            ("HOU_LOOP610_NORTH", "HOU_I45_UNDERPASS", "I-45 North Main Segment 2", "motorway", 75, 4800, False),
            ("HOU_I45_UNDERPASS", "HOU_I10_WHITEOAK", "I-45 / I-10 Interchange Bridge", "motorway", 70, 5000, True),
            ("HOU_I10_WHITEOAK", "HOU_DOWNTOWN_CORE", "Pierce Elevated / Houston Ave", "motorway", 70, 4800, True),
            ("HOU_BUFFALO_BAYOU_PK", "HOU_DOWNTOWN_CORE", "Walker / McKinney St Connector", "secondary", 35, 1800, False),
            ("HOU_DOWNTOWN_CORE", "HOU_GRB_SHELTER", "Avenida de las Americas", "primary", 40, 2500, False),
            ("HOU_DOWNTOWN_CORE", "HOU_TOYOTA_CENTER", "Polk / Bell St Relief Way", "primary", 40, 2400, False),
            ("HOU_GRB_SHELTER", "HOU_TOYOTA_CENTER", "Chartres St Downtown Link", "secondary", 35, 2000, False),
            ("HOU_WESTHEIMER", "HOU_RICE_UNIV", "Montrose / Sunset Boulevard", "primary", 45, 2200, False),
            ("HOU_RICE_UNIV", "HOU_MED_CENTER", "Main Street / Fannin Spine", "primary", 45, 2600, False),
            ("HOU_MED_CENTER", "HOU_NRG_PARK", "Fannin South Extension", "primary", 50, 3000, False),
            ("HOU_MED_CENTER", "HOU_UH_CAMPUS", "Holcombe Blvd - OST Link", "primary", 45, 2400, False),
            ("HOU_TOYOTA_CENTER", "HOU_UH_CAMPUS", "I-69 / TX-288 South Fwy", "motorway", 75, 4500, False),
            ("HOU_NRG_PARK", "HOU_LOOP610_SOUTH", "Loop 610 South Fwy Connector", "motorway", 80, 5000, False),
            ("HOU_UH_CAMPUS", "HOU_EAST_END", "Wayside Dr / Harrisburg Blvd", "primary", 45, 2200, False),
            ("HOU_DOWNTOWN_CORE", "HOU_I10_EAST", "I-10 East Freeway", "motorway", 80, 5200, False),
            ("HOU_I10_EAST", "HOU_EAST_END", "Lockwood Dr / Buffalo Bayou Bridge", "primary", 40, 2000, True)
        ]

        self._add_bidirectional_edges(G, edges_data)
        return G

    def _add_bidirectional_edges(self, G: nx.DiGraph, edges_data: List[Tuple]):
        """Helper to inject bidirectional edges with calculated distances and geometry."""
        for u, v, name, highway, speed, capacity, is_bridge in edges_data:
            lat_u, lon_u = G.nodes[u]["lat"], G.nodes[u]["lon"]
            lat_v, lon_v = G.nodes[v]["lat"], G.nodes[v]["lon"]
            dist = haversine_distance(lat_u, lon_u, lat_v, lon_v)

            # Forward edge
            fwd_id = f"{u}__{v}"
            G.add_edge(
                u, v,
                id=fwd_id,
                name=name,
                highway=highway,
                length=round(dist, 1),
                speed_limit=speed,
                capacity=capacity,
                is_bridge=is_bridge,
                geometry=[[lat_u, lon_u], [lat_v, lon_v]]
            )

            # Backward edge
            rev_id = f"{v}__{u}"
            G.add_edge(
                v, u,
                id=rev_id,
                name=name,
                highway=highway,
                length=round(dist, 1),
                speed_limit=speed,
                capacity=capacity,
                is_bridge=is_bridge,
                geometry=[[lat_v, lon_v], [lat_u, lon_u]]
            )
