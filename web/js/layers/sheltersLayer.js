/**
 * AquaRoute AI - Emergency Shelters Layer Module
 * Renders designated safe hubs, capacity gauges, and elevations.
 */

window.SheltersLayer = {
  create: function(sheltersGeoJson) {
    if (!sheltersGeoJson || !sheltersGeoJson.features) return L.layerGroup();

    return L.geoJSON(sheltersGeoJson, {
      pointToLayer: function(feature, latlng) {
        const customIcon = L.divIcon({
          className: 'shelter-marker',
          html: `
            <div style="
              width: 26px;
              height: 26px;
              background: #10b981;
              border: 2px solid #ffffff;
              border-radius: 6px;
              display: flex;
              align-items: center;
              justify-content: center;
              color: white;
              font-size: 13px;
              box-shadow: 0 0 12px rgba(16, 185, 129, 0.8);
            ">🛡️</div>
          `,
          iconSize: [26, 26],
          iconAnchor: [13, 13]
        });

        return L.marker(latlng, { icon: customIcon });
      },
      onEachFeature: function(feature, layer) {
        const props = feature.properties || {};
        const cap = props.capacity ? props.capacity.toLocaleString() : '20,000';

        layer.bindPopup(`
          <div style="font-family:sans-serif; font-size:13px; min-width:200px; color:#1f2937;">
            <h4 style="margin:0 0 6px 0; color:#10b981;">🛡️ ${props.name}</h4>
            <div style="font-size:12px; margin-bottom:4px;"><strong>Safe Capacity:</strong> ${cap} people</div>
            <div style="font-size:12px; margin-bottom:4px;"><strong>Elevation ASL:</strong> ${props.elevation_m} m</div>
            <div style="font-size:12px; color:#059669;"><strong>Status:</strong> Operational Safe Zone</div>
          </div>
        `);
      }
    });
  }
};
