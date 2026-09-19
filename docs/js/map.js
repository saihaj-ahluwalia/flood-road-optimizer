/**
 * AquaRoute AI - Leaflet Map Orchestrator
 */

window.AppMap = {
  map: null,
  layers: {
    hazard: null,
    roads: null,
    bottlenecks: null,
    shelters: null,
    routes: null
  },
  baseTileLayer: null,

  init: function() {
    if (this.map) return;

    // Dark Matter CartoDB Basemap for high-contrast tactical view
    this.map = L.map('map-canvas', {
      zoomControl: false,
      attributionControl: false
    }).setView([19.0760, 72.8777], 12);

    L.control.zoom({ position: 'bottomright' }).addTo(this.map);

    this.baseTileLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd'
    }).addTo(this.map);

    this.setupLayerControls();
  },

  updateScenarioLayers: function(scenarioData, onRoadClick) {
    if (!this.map || !scenarioData) return;

    // Center map on city
    if (scenarioData.city && scenarioData.city.center) {
      this.map.flyTo(scenarioData.city.center, scenarioData.city.zoom || 12, { duration: 1.2 });
    }

    // Clear existing layers
    Object.keys(this.layers).forEach(k => {
      if (this.layers[k]) {
        this.map.removeLayer(this.layers[k]);
        this.layers[k] = null;
      }
    });

    const geo = scenarioData.geo || {};

    // 1. Hazard Layer
    this.layers.hazard = window.HazardLayer.create(geo.hazard);
    if (document.getElementById('layer-toggle-hazard')?.checked) {
      this.layers.hazard.addTo(this.map);
    }

    // 2. Road Criticality Layer
    this.layers.roads = window.RoadsLayer.create(geo.roads, onRoadClick);
    if (document.getElementById('layer-toggle-roads')?.checked) {
      this.layers.roads.addTo(this.map);
    }

    // 3. Bottlenecks Layer
    this.layers.bottlenecks = window.BottlenecksLayer.create(geo.bottlenecks);
    if (document.getElementById('layer-toggle-bottlenecks')?.checked) {
      this.layers.bottlenecks.addTo(this.map);
    }

    // 4. Shelters Layer
    this.layers.shelters = window.SheltersLayer.create(geo.shelters);
    if (document.getElementById('layer-toggle-shelters')?.checked) {
      this.layers.shelters.addTo(this.map);
    }

    // 5. Evacuation Corridors Layer
    this.layers.routes = window.EvacuationLayer.create(geo.routes);
    if (document.getElementById('layer-toggle-routes')?.checked) {
      this.layers.routes.addTo(this.map);
    }
  },

  setupLayerControls: function() {
    const toggles = [
      { id: 'layer-toggle-hazard', layer: 'hazard' },
      { id: 'layer-toggle-roads', layer: 'roads' },
      { id: 'layer-toggle-bottlenecks', layer: 'bottlenecks' },
      { id: 'layer-toggle-shelters', layer: 'shelters' },
      { id: 'layer-toggle-routes', layer: 'routes' }
    ];

    toggles.forEach(t => {
      const el = document.getElementById(t.id);
      if (el) {
        el.addEventListener('change', (e) => {
          const lGroup = this.layers[t.layer];
          if (!lGroup) return;

          if (e.target.checked) {
            lGroup.addTo(this.map);
          } else {
            this.map.removeLayer(lGroup);
          }
        });
      }
    });
  }
};
