/**
 * AquaRoute AI - Bottlenecks & Choke Points Layer Module
 * Renders pulsing danger markers on critical bridge junctions and cutoff nodes.
 */

window.BottlenecksLayer = {
  create: function(bottlenecksGeoJson) {
    if (!bottlenecksGeoJson || !bottlenecksGeoJson.features) return L.layerGroup();

    return L.geoJSON(bottlenecksGeoJson, {
      pointToLayer: function(feature, latlng) {
        const props = feature.properties || {};
        const isCritical = props.severity === 'critical';
        const color = isCritical ? '#ef4444' : '#f97316';

        const customIcon = L.divIcon({
          className: 'bottleneck-marker',
          html: `
            <div style="
              width: 22px;
              height: 22px;
              background: ${color};
              border: 2px solid #ffffff;
              border-radius: 50%;
              display: flex;
              align-items: center;
              justify-content: center;
              color: white;
              font-size: 11px;
              box-shadow: 0 0 10px ${color};
            ">⚠️</div>
          `,
          iconSize: [22, 22],
          iconAnchor: [11, 11]
        });

        return L.marker(latlng, { icon: customIcon });
      },
      onEachFeature: function(feature, layer) {
        const props = feature.properties || {};
        layer.bindPopup(`
          <div style="font-family:sans-serif; font-size:13px; min-width:180px; color:#1f2937;">
            <h4 style="margin:0 0 6px 0; color:#ef4444;">⚠️ ${props.name}</h4>
            <div style="font-size:12px; margin-bottom:4px;"><strong>Risk Type:</strong> ${props.type}</div>
            <div style="font-size:12px; margin-bottom:4px;"><strong>Network Cutoff Loss:</strong> ${props.degree_loss_pct}%</div>
            <div style="font-size:12px; margin-bottom:4px;"><strong>Incoming Evac Flow:</strong> ${props.in_flow_vehicles} vehicles</div>
            <div style="font-size:12px;"><strong>Flood Inundation:</strong> ${props.flood_depth_m} m</div>
          </div>
        `);
      }
    });
  }
};
