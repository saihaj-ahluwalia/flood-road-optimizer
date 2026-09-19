/**
 * AquaRoute AI - Analytics & Chart.js Visualizations Module
 */

window.AppCharts = {
  cvrChart: null,
  tierChart: null,

  initOrUpdate: function(scenarioData) {
    if (!scenarioData || !scenarioData.geo || !scenarioData.geo.roads) return;

    const roads = scenarioData.geo.roads.features || [];

    // 1. Prepare Top Flow vs Capacity Corridors
    const topRoads = [...roads]
      .sort((a, b) => (b.properties.flow_volume || 0) - (a.properties.flow_volume || 0))
      .slice(0, 6);

    const labels = topRoads.map(r => {
      const n = r.properties.name || 'Road';
      return n.length > 15 ? n.substring(0, 14) + '…' : n;
    });
    const flows = topRoads.map(r => r.properties.flow_volume || 0);
    const capacities = topRoads.map(r => r.properties.capacity || 2000);

    // 2. Prepare Tier Counts
    let tier1 = 0, tier2 = 0, tier3 = 0, tier4 = 0;
    roads.forEach(r => {
      const score = r.properties.criticality_score || 0;
      if (score >= 75) tier1++;
      else if (score >= 55) tier2++;
      else if (score >= 35) tier3++;
      else tier4++;
    });

    this.renderCvrChart(labels, flows, capacities);
    this.renderTierChart([tier1, tier2, tier3, tier4]);
  },

  renderCvrChart: function(labels, flows, capacities) {
    const ctx = document.getElementById('chart-cvr');
    if (!ctx) return;

    if (this.cvrChart) {
      this.cvrChart.destroy();
    }

    this.cvrChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Evac Flow (veh)',
            data: flows,
            backgroundColor: '#38bdf8',
            borderRadius: 4
          },
          {
            label: 'Road Capacity',
            data: capacities,
            backgroundColor: 'rgba(75, 85, 99, 0.6)',
            borderRadius: 4
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#9ca3af', font: { size: 10 } }
          }
        },
        scales: {
          x: {
            ticks: { color: '#9ca3af', font: { size: 9 } },
            grid: { color: 'rgba(255,255,255,0.05)' }
          },
          y: {
            ticks: { color: '#9ca3af', font: { size: 9 } },
            grid: { color: 'rgba(255,255,255,0.05)' }
          }
        }
      }
    });
  },

  renderTierChart: function(tierCounts) {
    const ctx = document.getElementById('chart-tiers');
    if (!ctx) return;

    if (this.tierChart) {
      this.tierChart.destroy();
    }

    this.tierChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: ['Tier 1 Lifeline', 'Tier 2 High', 'Tier 3 Moderate', 'Tier 4 Resilient'],
        datasets: [
          {
            data: tierCounts,
            backgroundColor: ['#ef4444', '#f97316', '#eab308', '#10b981'],
            borderWidth: 1,
            borderColor: '#111827'
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: { color: '#9ca3af', font: { size: 10 } }
          }
        }
      }
    });
  }
};
