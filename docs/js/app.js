/**
 * AquaRoute AI - Master Application Controller
 */

window.AquaApp = {
  currentCity: 'mumbai',
  currentScenario: 'moderate',
  scenarioData: null,

  init: function() {
    window.AppMap.init();
    this.setupUIEvents();
    this.loadScenario(this.currentCity, this.currentScenario);
  },

  loadScenario: async function(city, scenario) {
    this.currentCity = city;
    this.currentScenario = scenario;

    const dataPath = `data/${city}_${scenario}.json`;

    try {
      const resp = await fetch(dataPath);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      this.scenarioData = await resp.json();
    } catch (e) {
      console.warn(`Fetch failed for ${dataPath}, trying fallback path:`, e);
      try {
        const altPath = `../data/scenarios/${city}_${scenario}.json`;
        const resp2 = await fetch(altPath);
        this.scenarioData = await resp2.json();
      } catch (e2) {
        console.error('All data fetches failed:', e2);
        return;
      }
    }

    this.renderScenarioData();
  },

  renderScenarioData: function() {
    const data = this.scenarioData;
    if (!data) return;

    // 1. Update Map Layers
    window.AppMap.updateScenarioLayers(data, (roadProps) => {
      this.showRoadInspector(roadProps);
    });

    // 2. Update Charts
    window.AppCharts.initOrUpdate(data);

    // 3. Initialize Sandbox
    window.InterventionSandbox.init(data);

    // 4. Update HUD Header & Scorecards
    const m = data.metrics || {};
    const sc = data.scenario || {};

    const elResilience = document.getElementById('val-resilience');
    const elFillResilience = document.getElementById('fill-resilience');
    const elScName = document.getElementById('txt-scenario-name');
    const elScDesc = document.getElementById('txt-scenario-desc');
    const elRain = document.getElementById('val-rain');
    const elSurge = document.getElementById('val-surge');
    const elDuration = document.getElementById('val-duration');
    const elEvac = document.getElementById('val-evacuees');
    const elTime = document.getElementById('val-time');
    const elSub = document.getElementById('val-submerged');
    const elSubPct = document.getElementById('val-submerged-pct');
    const elChoke = document.getElementById('val-chokepoints');
    const elLifeCount = document.getElementById('txt-lifeline-count');

    if (elResilience) elResilience.textContent = `${m.network_resilience_index || 75.0}%`;
    if (elFillResilience) elFillResilience.style.width = `${m.network_resilience_index || 75.0}%`;

    if (elScName) elScName.textContent = sc.name || 'Disaster Scenario';
    if (elScDesc) elScDesc.textContent = sc.description || '';
    if (elRain) elRain.textContent = `${sc.rainfall_mm_hr || 50} mm/hr`;
    if (elSurge) elSurge.textContent = `${sc.surge_m || 0.5} m`;
    if (elDuration) elDuration.textContent = `${sc.duration_hrs || 12} hrs`;

    if (elEvac) elEvac.textContent = (m.total_evac_vehicles || 0).toLocaleString();
    if (elTime) elTime.innerHTML = `${m.avg_travel_time_min || 0} <span style="font-size:12px;">min</span>`;
    if (elSub) elSub.innerHTML = `${m.submerged_road_km || 0} <span style="font-size:12px;">km</span>`;
    if (elSubPct) elSubPct.textContent = `${m.submerged_percentage || 0}% network cutoff`;
    if (elChoke) elChoke.textContent = m.critical_chokepoints_count || 0;
    if (elLifeCount) elLifeCount.textContent = `${m.tier1_lifelines_count || 0} Critical`;

    // 5. Populate Interventions Queue
    this.populateInterventionsList(data.interventions || {});

    // 6. Populate Shelters Status
    this.populateSheltersStatus(data.geo?.shelters?.features || []);
  },

  populateInterventionsList: function(interventions) {
    const container = document.getElementById('interventions-container');
    if (!container) return;

    container.innerHTML = '';
    const items = interventions.priority_interventions || [];

    if (items.length === 0) {
      container.innerHTML = '<div style="font-size:12px; color:var(--text-dim);">No critical lifelines compromised.</div>';
      return;
    }

    items.forEach(item => {
      const card = document.createElement('div');
      card.className = 'intervention-card';
      card.innerHTML = `
        <div class="intervention-head">
          <span class="intervention-rank">#${item.rank}</span>
          <span class="intervention-road">${item.target_road}</span>
          <span class="intervention-badge badge-tier1">RCS ${item.criticality_score}</span>
        </div>
        <div style="font-size:11px; color:var(--text-dim);">${item.from_to}</div>
        <div class="intervention-action">
          <strong style="color:var(--accent-cyan);">Action:</strong> ${item.action_summary}
        </div>
      `;

      card.addEventListener('click', () => {
        // Find road feature and trigger inspector
        const roads = this.scenarioData.geo.roads.features || [];
        const r = roads.find(x => x.properties.id === item.road_id || x.properties.name === item.target_road);
        if (r) {
          this.showRoadInspector(r.properties);
        }
      });

      container.appendChild(card);
    });
  },

  populateSheltersStatus: function(shelters) {
    const container = document.getElementById('shelters-status-container');
    if (!container) return;

    container.innerHTML = '';
    shelters.forEach(s => {
      const p = s.properties || {};
      const card = document.createElement('div');
      card.className = 'intervention-card';
      card.style.borderColor = 'rgba(16, 185, 129, 0.3)';
      card.innerHTML = `
        <div class="intervention-head">
          <span style="color:#10b981; font-weight:600;">🛡️ ${p.name}</span>
          <span class="intervention-badge" style="background:rgba(16,185,129,0.2); color:#34d399;">Active</span>
        </div>
        <div style="font-size:11px; color:var(--text-muted); display:flex; justify-content:space-between;">
          <span>Capacity: ${(p.capacity || 20000).toLocaleString()} people</span>
          <span>Elevation: ${p.elevation_m}m ASL</span>
        </div>
      `;
      container.appendChild(card);
    });
  },

  showRoadInspector: function(p) {
    const inspector = document.getElementById('floating-inspector');
    if (!inspector) return;

    document.getElementById('ins-name').textContent = p.name || 'Corridor';
    document.getElementById('ins-nodes').textContent = `${p.from_node || 'Start'} ➔ ${p.to_node || 'End'}`;
    document.getElementById('ins-rcs').textContent = p.criticality_score || '0';
    document.getElementById('ins-rcs').style.color = p.tier_color || '#10b981';
    document.getElementById('ins-depth').textContent = `${(p.flood_depth_m || 0).toFixed(2)} m`;
    document.getElementById('ins-flow').textContent = `${(p.flow_volume || 0).toLocaleString()} veh`;
    document.getElementById('ins-speed').textContent = `${p.speed_kmh || 50} km/h`;
    document.getElementById('ins-action').textContent = p.action || 'Standard emergency operation.';

    const btnMitigate = document.getElementById('btn-ins-mitigate');
    btnMitigate.onclick = () => {
      window.InterventionSandbox.openWithRoad(p);
    };

    inspector.classList.add('active');
  },

  setupUIEvents: function() {
    // City Selector Buttons
    document.querySelectorAll('.city-selector .btn-pill').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.city-selector .btn-pill').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const city = btn.dataset.city;
        this.loadScenario(city, this.currentScenario);
      });
    });

    // Scenario Selector Buttons
    document.querySelectorAll('.scenario-selector .btn-pill').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.scenario-selector .btn-pill').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const sc = btn.dataset.scenario;
        this.loadScenario(this.currentCity, sc);
      });
    });

    // Toggle Left & Right Panels
    const btnToggleLeft = document.getElementById('btn-toggle-left');
    const hudLeft = document.getElementById('hud-left');
    if (btnToggleLeft && hudLeft) {
      btnToggleLeft.addEventListener('click', () => {
        hudLeft.classList.toggle('collapsed-left');
      });
    }

    const btnToggleRight = document.getElementById('btn-toggle-right');
    const hudRight = document.getElementById('hud-right');
    if (btnToggleRight && hudRight) {
      btnToggleRight.addEventListener('click', () => {
        hudRight.classList.toggle('collapsed-right');
      });
    }

    // Inspector Close
    const btnCloseIns = document.getElementById('btn-close-inspector');
    if (btnCloseIns) {
      btnCloseIns.addEventListener('click', () => {
        document.getElementById('floating-inspector')?.classList.remove('active');
      });
    }

    // Modals
    const modalSandbox = document.getElementById('modal-sandbox');
    const btnOpenSandbox = document.getElementById('btn-sandbox');
    const btnCloseSandbox = document.getElementById('btn-close-sandbox');
    const btnCancelSandbox = document.getElementById('btn-cancel-sandbox');
    const btnApplySandbox = document.getElementById('btn-apply-sandbox');

    if (btnOpenSandbox) {
      btnOpenSandbox.addEventListener('click', () => {
        modalSandbox?.classList.add('active');
      });
    }
    [btnCloseSandbox, btnCancelSandbox].forEach(b => {
      if (b) b.addEventListener('click', () => modalSandbox?.classList.remove('active'));
    });

    if (btnApplySandbox) {
      btnApplySandbox.addEventListener('click', () => {
        modalSandbox?.classList.remove('active');
        // Visual confirmation
        alert('Mitigation strategy applied to simulation model! Network resilience boosted.');
      });
    }

    // Report Modal
    const modalReport = document.getElementById('modal-report');
    const btnOpenReport = document.getElementById('btn-report');
    const btnCloseReport = document.getElementById('btn-close-report');
    const btnCancelReport = document.getElementById('btn-cancel-report');
    const btnDownloadPdf = document.getElementById('btn-download-pdf');

    if (btnOpenReport) {
      btnOpenReport.addEventListener('click', () => {
        this.populateReportModal();
        modalReport?.classList.add('active');
      });
    }
    [btnCloseReport, btnCancelReport].forEach(b => {
      if (b) b.addEventListener('click', () => modalReport?.classList.remove('active'));
    });

    if (btnDownloadPdf) {
      btnDownloadPdf.addEventListener('click', () => {
        const element = document.getElementById('report-printable-area');
        if (element && window.html2pdf) {
          const opt = {
            margin: 10,
            filename: `AquaRoute_EOC_Briefing_${this.currentCity}_${this.currentScenario}.pdf`,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
          };
          window.html2pdf().set(opt).from(element).save();
        }
      });
    }
  },

  populateReportModal: function() {
    const data = this.scenarioData;
    if (!data) return;

    const city = data.city || {};
    const sc = data.scenario || {};
    const m = data.metrics || {};
    const interventions = data.interventions || {};

    const elTitle = document.getElementById('rep-city-title');
    const elTs = document.getElementById('rep-timestamp');
    const elSub = document.getElementById('rep-submerged');
    const elLife = document.getElementById('rep-lifelines');
    const elEvac = document.getElementById('rep-evacuees');
    const tbody = document.getElementById('rep-table-body');

    if (elTitle) elTitle.textContent = `${city.name.toUpperCase()} FLOOD DISASTER ROAD CRITICALITY REPORT`;
    if (elTs) elTs.textContent = `Generated: ${new Date().toISOString().split('T')[0]} | Scenario: ${sc.name} | AquaRoute AI Engine`;
    if (elSub) elSub.textContent = `${m.submerged_road_km || 0} km (${m.submerged_percentage || 0}%)`;
    if (elLife) elLife.textContent = `${m.tier1_lifelines_count || 0} Corridors`;
    if (elEvac) elEvac.textContent = `${(m.total_evac_vehicles || 0).toLocaleString()} Vehicles`;

    if (tbody) {
      tbody.innerHTML = '';
      const items = interventions.priority_interventions || [];
      items.forEach(it => {
        const tr = document.createElement('tr');
        tr.style.borderBottom = '1px solid rgba(255,255,255,0.08)';
        tr.innerHTML = `
          <td style="padding:8px; font-weight:bold; color:#38bdf8;">#${it.rank}</td>
          <td style="padding:8px; color:#fff;">${it.target_road}</td>
          <td style="padding:8px; color:#ef4444; font-weight:bold;">${it.criticality_score}</td>
          <td style="padding:8px;">${it.flood_depth_m} m</td>
          <td style="padding:8px; color:#9ca3af;">${it.action_summary}</td>
        `;
        tbody.appendChild(tr);
      });
    }
  }
};

// Start app on DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
  window.AquaApp.init();
});
