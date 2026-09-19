"""
AquaRoute AI - Configuration & City Geographic Profiles
Contains spatial bounds, emergency shelters, water bodies, elevation baselines,
and flood scenario profiles for Mumbai, Jakarta, and Houston.
"""

from typing import Dict, Any, List

CITIES_CONFIG: Dict[str, Dict[str, Any]] = {
    "mumbai": {
        "id": "mumbai",
        "name": "Mumbai",
        "country": "India",
        "center": [19.0760, 72.8777],  # [lat, lon]
        "zoom": 12,
        "bbox": {
            "min_lat": 18.9800,
            "max_lat": 19.1600,
            "min_lon": 72.8100,
            "max_lon": 72.9500
        },
        "description": "Monsoonal deluge, Mithi River basin overflow, coastal tidal surge affecting Western & Eastern Express Highways.",
        "elevation_baseline": 6.0,  # meters above sea level average
        "water_bodies": [
            {"name": "Arabian Sea Coast", "type": "ocean", "coords": [[18.98, 72.81], [19.05, 72.82], [19.12, 72.81], [19.16, 72.82]]},
            {"name": "Mithi River", "type": "river", "coords": [[19.055, 72.865], [19.068, 72.875], [19.085, 72.880], [19.115, 72.895]]},
            {"name": "Mahim Creek", "type": "creek", "coords": [[19.040, 72.835], [19.048, 72.845], [19.052, 72.860]]},
            {"name": "Thane Creek", "type": "creek", "coords": [[19.000, 72.940], [19.080, 72.950], [19.160, 72.945]]}
        ],
        "vulnerable_hotspots": [
            {"name": "Hindmata - Dadar Lowland", "lat": 19.0180, "lon": 72.8430, "elevation": 3.2, "vuln_weight": 1.4},
            {"name": "Kurla West - Mithi River Zone", "lat": 19.0680, "lon": 72.8780, "elevation": 4.1, "vuln_weight": 1.6},
            {"name": "Bandra-Kurla Complex (BKC)", "lat": 19.0620, "lon": 72.8650, "elevation": 5.0, "vuln_weight": 1.3},
            {"name": "Milan Subway Underpass", "lat": 19.0890, "lon": 72.8450, "elevation": 2.5, "vuln_weight": 1.8},
            {"name": "Sion Circle - Matunga", "lat": 19.0380, "lon": 72.8600, "elevation": 3.8, "vuln_weight": 1.5},
            {"name": "Andheri Subway & SV Road", "lat": 19.1190, "lon": 72.8460, "elevation": 4.5, "vuln_weight": 1.5},
            {"name": "Dharavi Junction", "lat": 19.0440, "lon": 72.8550, "elevation": 3.9, "vuln_weight": 1.7}
        ],
        "shelters": [
            {"id": "sh_mum_1", "name": "BKC MMRDA Relief Center", "lat": 19.0650, "lon": 72.8690, "capacity": 25000, "elevation": 12.0, "status": "active"},
            {"id": "sh_mum_2", "name": "Shivaji Park Emergency Complex", "lat": 19.0270, "lon": 72.8380, "capacity": 18000, "elevation": 9.5, "status": "active"},
            {"id": "sh_mum_3", "name": "IIT Bombay Powai High Grounds", "lat": 19.1330, "lon": 72.9150, "capacity": 30000, "elevation": 45.0, "status": "active"},
            {"id": "sh_mum_4", "name": "Andheri Sports Complex Relief Hub", "lat": 19.1310, "lon": 72.8350, "capacity": 15000, "elevation": 14.0, "status": "active"},
            {"id": "sh_mum_5", "name": "Somaiya Vidyavihar Safe Campus", "lat": 19.0730, "lon": 72.8990, "capacity": 22000, "elevation": 18.0, "status": "active"}
        ],
        "scenarios": {
            "mild": {
                "name": "Monsoon Surge (10-Year Return)",
                "rainfall_mm_hr": 45.0,
                "surge_m": 0.4,
                "duration_hrs": 6,
                "description": "Standard high-intensity monsoon rainfall with localized waterlogging in subways and known depressions."
            },
            "moderate": {
                "name": "Severe Deluge (50-Year Return)",
                "rainfall_mm_hr": 85.0,
                "surge_m": 1.1,
                "duration_hrs": 12,
                "description": "Mithi River bank overtopping combined with high tide peak (4.5m tide), inundating arterial roads."
            },
            "severe": {
                "name": "Catastrophic Cloudburst (100-Year Return)",
                "rainfall_mm_hr": 140.0,
                "surge_m": 2.2,
                "duration_hrs": 24,
                "description": "Extreme 2005-scale deluge (>900mm in 24h) with total river basin breaching and widespread arterial cutoffs."
            }
        }
    },
    "jakarta": {
        "id": "jakarta",
        "name": "Jakarta",
        "country": "Indonesia",
        "center": [-6.2088, 106.8456],
        "zoom": 12,
        "bbox": {
            "min_lat": -6.3200,
            "max_lat": -6.1100,
            "min_lon": 106.7400,
            "max_lon": 106.9400
        },
        "description": "Rapid land subsidence, Ciliwung River overflow, and northern coastal 'Banjir Rob' tidal inundation.",
        "elevation_baseline": 3.5,
        "water_bodies": [
            {"name": "Jakarta Bay (North Sea)", "type": "ocean", "coords": [[-6.11, 106.74], [-6.11, 106.84], [-6.11, 106.94]]},
            {"name": "Ciliwung River", "type": "river", "coords": [[-6.30, 106.86], [-6.24, 106.85], [-6.18, 106.83], [-6.12, 106.82]]},
            {"name": "Banjir Kanal Barat (West Flood Canal)", "type": "canal", "coords": [[-6.22, 106.84], [-6.19, 106.80], [-6.13, 106.78]]},
            {"name": "Banjir Kanal Timur (East Flood Canal)", "type": "canal", "coords": [[-6.23, 106.87], [-6.19, 106.91], [-6.12, 106.94]]}
        ],
        "vulnerable_hotspots": [
            {"name": "Pluit & Muara Baru Subsidence Basin", "lat": -6.1250, "lon": 106.7950, "elevation": -1.8, "vuln_weight": 1.9},
            {"name": "Kelapa Gading Lowlands", "lat": -6.1580, "lon": 106.9050, "elevation": 0.8, "vuln_weight": 1.6},
            {"name": "Kampung Melayu - Ciliwung Basin", "lat": -6.2280, "lon": 106.8650, "elevation": 2.2, "vuln_weight": 1.7},
            {"name": "Grogol - Trisakti Junction", "lat": -6.1680, "lon": 106.7890, "elevation": 1.5, "vuln_weight": 1.5},
            {"name": "Bidara Cina Fluvial Zone", "lat": -6.2410, "lon": 106.8680, "elevation": 3.0, "vuln_weight": 1.6},
            {"name": "Ancol Coastal Gate", "lat": -6.1260, "lon": 106.8420, "elevation": -0.5, "vuln_weight": 1.8}
        ],
        "shelters": [
            {"id": "sh_jkt_1", "name": "Monas National Monument Relief Base", "lat": -6.1754, "lon": 106.8272, "capacity": 35000, "elevation": 15.0, "status": "active"},
            {"id": "sh_jkt_2", "name": "Gelora Bung Karno (GBK) Stadium Hub", "lat": -6.2185, "lon": 106.8018, "capacity": 45000, "elevation": 16.5, "status": "active"},
            {"id": "sh_jkt_3", "name": "Halim Perdanakusuma Relief Depot", "lat": -6.2650, "lon": 106.8900, "capacity": 20000, "elevation": 28.0, "status": "active"},
            {"id": "sh_jkt_4", "name": "Jakarta International Velodrome", "lat": -6.1920, "lon": 106.8910, "capacity": 18000, "elevation": 14.0, "status": "active"},
            {"id": "sh_jkt_5", "name": "Universitas Indonesia Campus Center", "lat": -6.3600, "lon": 106.8300, "capacity": 30000, "elevation": 55.0, "status": "active"}
        ],
        "scenarios": {
            "mild": {
                "name": "Banjir Rob & Seasonal Rain (10-Year)",
                "rainfall_mm_hr": 40.0,
                "surge_m": 0.5,
                "duration_hrs": 6,
                "description": "High sea tide causing northern coastal sea-wall seepage and localized canal overflow."
            },
            "moderate": {
                "name": "Heavy Fluvial Torrent (50-Year)",
                "rainfall_mm_hr": 80.0,
                "surge_m": 1.2,
                "duration_hrs": 12,
                "description": "Upstream Katulampa dam emergency release coupled with intense urban downpour inundating Ciliwung banks."
            },
            "severe": {
                "name": "Super-Tide & Megacity Deluge (100-Year)",
                "rainfall_mm_hr": 135.0,
                "surge_m": 2.4,
                "duration_hrs": 24,
                "description": "Sea-wall breach in North Jakarta + simultaneous peak Ciliwung fluvial flood blocking main ring roads."
            }
        }
    },
    "houston": {
        "id": "houston",
        "name": "Houston",
        "country": "United States",
        "center": [29.7604, -95.3698],
        "zoom": 12,
        "bbox": {
            "min_lat": 29.6500,
            "max_lat": 29.8800,
            "min_lon": -95.5200,
            "max_lon": -95.2200
        },
        "description": "Extreme hurricane precipitation, low-gradient bayou system overtopping, and freeway underpass inundation.",
        "elevation_baseline": 14.0,
        "water_bodies": [
            {"name": "Buffalo Bayou", "type": "bayou", "coords": [[29.775, -95.500], [29.762, -95.420], [29.761, -95.360], [29.750, -95.280]]},
            {"name": "White Oak Bayou", "type": "bayou", "coords": [[29.840, -95.450], [29.790, -95.390], [29.765, -95.362]]},
            {"name": "Brays Bayou", "type": "bayou", "coords": [[29.700, -95.500], [29.690, -95.400], [29.705, -95.300]]},
            {"name": "Houston Ship Channel", "type": "channel", "coords": [[29.750, -95.280], [29.740, -95.220], [29.720, -95.150]]}
        ],
        "vulnerable_hotspots": [
            {"name": "I-10 & White Oak Bayou Interchange", "lat": 29.7750, "lon": -95.3720, "elevation": 9.2, "vuln_weight": 1.8},
            {"name": "Downtown Buffalo Bayou Park Underpasses", "lat": 29.7610, "lon": -95.3750, "elevation": 8.5, "vuln_weight": 1.7},
            {"name": "Loop 610 & Brays Bayou Basin (Meyerland)", "lat": 29.6880, "lon": -95.4600, "elevation": 11.0, "vuln_weight": 1.6},
            {"name": "I-45 North Main Underpass", "lat": 29.7820, "lon": -95.3650, "elevation": 9.8, "vuln_weight": 1.7},
            {"name": "Addicks Reservoir Spillway Zone", "lat": 29.7880, "lon": -95.5100, "elevation": 13.5, "vuln_weight": 1.5},
            {"name": "East End / Harrisburg Channel Fringe", "lat": 29.7350, "lon": -95.3050, "elevation": 7.8, "vuln_weight": 1.5}
        ],
        "shelters": [
            {"id": "sh_hou_1", "name": "George R. Brown Convention Center", "lat": 29.7522, "lon": -95.3582, "capacity": 40000, "elevation": 16.0, "status": "active"},
            {"id": "sh_hou_2", "name": "NRG Park Multi-Disaster Mega Shelter", "lat": 29.6847, "lon": -95.4107, "capacity": 50000, "elevation": 21.0, "status": "active"},
            {"id": "sh_hou_3", "name": "Toyota Center Emergency Complex", "lat": 29.7508, "lon": -95.3621, "capacity": 18000, "elevation": 17.5, "status": "active"},
            {"id": "sh_hou_4", "name": "Rice University Campus Safe Zone", "lat": 29.7174, "lon": -95.4018, "capacity": 22000, "elevation": 22.0, "status": "active"},
            {"id": "sh_hou_5", "name": "University of Houston High Ground Shelter", "lat": 29.7199, "lon": -95.3422, "capacity": 25000, "elevation": 19.5, "status": "active"}
        ],
        "scenarios": {
            "mild": {
                "name": "Tropical Depression (10-Year)",
                "rainfall_mm_hr": 38.0,
                "surge_m": 0.3,
                "duration_hrs": 6,
                "description": "Rapid convective thunderstorm cells causing flash ponding on feeder roads and depressed bayou greenways."
            },
            "moderate": {
                "name": "Category 2 Tropical Storm (50-Year)",
                "rainfall_mm_hr": 75.0,
                "surge_m": 0.9,
                "duration_hrs": 14,
                "description": "Sustained rainfall exceeding bayou bank capacity; major interstate underpass closures."
            },
            "severe": {
                "name": "Hurricane Harvey Benchmark (500-Year)",
                "rainfall_mm_hr": 130.0,
                "surge_m": 1.8,
                "duration_hrs": 36,
                "description": "Historic stalled hurricane system (>1000mm cumulative), uncontrolled reservoir spillway releases."
            }
        }
    }
}

# Vehicle flood thresholds (meters)
CRITICAL_WATER_DEPTHS = {
    "dry": 0.05,            # Normal driving
    "minor_ponding": 0.15,  # Speed reduced by 25%
    "moderate_water": 0.30, # High risk, passenger cars stall
    "severe_flood": 0.50,   # Impassable for standard vehicles, emergency 4x4 only
    "total_submersion": 0.75 # Completely impassable for all vehicles
}

# Road prioritization weights
SCORING_WEIGHTS = {
    "betweenness_centrality": 0.30,
    "flow_volume_pressure": 0.25,
    "flood_vulnerability": 0.25,
    "isolation_risk": 0.20
}
