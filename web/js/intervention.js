/**
 * AquaRoute AI - What-If Mitigation Sandbox Engine
 * Simulates real-time engineering and first-responder countermeasures.
 */

window.InterventionSandbox = {
  currentRoads: [],
  selectedRoad: null,

  init: function(scenarioData) {
    if (!scenarioData || !scenarioData.geo || !scenarioData.geo.roads) return;

    this.currentRoads = scenarioData.geo.roads.features || [];
    this.populateRoadDropdown();
    this.setupEventListeners();
  },

  populateRoadDropdown: function() {
    const select = document.getElementById('sandbox-road-select');
    if (!select) return;

    select.innerHTML = '';
    // Filter to critical/vulnerable roads
    const candidateRoads = this.currentRoads.filter(r => r.properties.criticality_score >= 40 || r.properties.flood_depth_m > 0.15);
    const list = candidateRoads.length > 0 ? candidateRoads : this.currentRoads.slice(0, 10);

    list.forEach((r, idx) => {
      const opt = document.createElement('option');
      opt.value = r.properties.id;
      opt.textContent = `${r.properties.name} (RCS: ${r.properties.criticality_score}, Depth: ${r.properties.flood_depth_m}m)`;
      select.appendChild(opt);
    });

    if (list.length > 0) {
      this.selectedRoad = list[0];
      this.calculateSandboxImpact();
    }
  },

  setupEventListeners: function() {
    const roadSelect = document.getElementById('sandbox-road-select');
    const stratSelect = document.getElementById('sandbox-strategy-select');

    if (roadSelect) {
      roadSelect.addEventListener('change', (e) => {
        const rId = e.target.value;
        this.selectedRoad = this.currentRoads.find(r => r.properties.id === rId);
        this.calculateSandboxImpact();
      });
    }

    if (stratSelect) {
      stratSelect.addEventListener('change', () => {
        this.calculateSandboxImpact();
      });
    }
  },

  calculateSandboxImpact: function() {
    if (!this.selectedRoad) return;

    const props = this.selectedRoad.properties;
    const stratSelect = document.getElementById('sandbox-strategy-select');
    const strategy = stratSelect ? stratSelect.value : 'pump';

    const currentDepth = props.flood_depth_m || 0.3;
    const currentSpeed = props.speed_kmh || 20;
    const flow = props.flow_volume || 2500;

    let depthReduction = 0;
    let speedGain = 0;
    let vehCleared = 0;
    let resilienceBoost = 0;

    if (strategy === 'pump') {
      depthReduction = Math.min(currentDepth, 0.35);
      speedGain = Math.round(30 * (depthReduction / Math.max(0.1, currentDepth)));
      vehCleared = Math.round(flow * 0.45);
      resilienceBoost = 8.5;
    } else if (strategy === 'barrier') {
      depthReduction = Math.min(currentDepth, 0.55);
      speedGain = Math.round(40 * (depthReduction / Math.max(0.1, currentDepth)));
      vehCleared = Math.round(flow * 0.60);
      resilienceBoost = 12.0;
    } else if (strategy === 'contraflow') {
      depthReduction = 0.05;
      speedGain = 25;
      vehCleared = Math.round(flow * 0.75);
      resilienceBoost = 10.5;
    } else if (strategy === 'all') {
      depthReduction = currentDepth;
      speedGain = 50;
      vehCleared = flow;
      resilienceBoost = 18.5;
    }

    // Update UI
    const elDepth = document.getElementById('sb-depth-red');
    const elSpeed = document.getElementById('sb-speed-gain');
    const elVeh = document.getElementById('sb-veh-cleared');
    const elRes = document.getElementById('sb-resilience-boost');

    if (elDepth) elDepth.textContent = `-${depthReduction.toFixed(2)} m`;
    if (elSpeed) elSpeed.textContent = `+${speedGain} km/h`;
    if (elVeh) elVeh.textContent = `+${vehCleared.toLocaleString()}`;
    if (elRes) elRes.textContent = `+${resilienceBoost.toFixed(1)}%`;
  },

  openWithRoad: function(roadProps) {
    const modal = document.getElementById('modal-sandbox');
    const select = document.getElementById('sandbox-road-select');
    if (modal) modal.classList.add('active');

    if (select && roadProps && roadProps.id) {
      select.value = roadProps.id;
      this.selectedRoad = this.currentRoads.find(r => r.properties.id === roadProps.id);
      this.calculateSandboxImpact();
    }
  }
};
