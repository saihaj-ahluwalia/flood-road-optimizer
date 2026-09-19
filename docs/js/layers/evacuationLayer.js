/**
 * AquaRoute AI - Evacuation Flow Corridors Layer Module
 * Renders animated dynamic flow paths from origins to safe shelters.
 */

window.EvacuationLayer = {
  create: function(routesGeoJson) {
    if (!routesGeoJson || !routesGeoJson.features) return L.layerGroup();

    return L.geoJSON(routesGeoJson, {
      style: function(feature) {
        const props = feature.properties || {};
        const isDelayed = props.is_severely_delayed;

        return {
          color: isDelayed ? '#c084fc' : '#a855f7',
          weight: 3,
          opacity: 0.7,
          dashArray: '8, 8',
          lineCap: 'round'
        };
      },
      onEachFeature: function(feature, layer) {
        const props = feature.properties || {};
        layer.bindTooltip(`
          <div style="font-family:sans-serif; font-size:12px; padding:2px;">
            <strong style="color:#a855f7;">⚡ Evacuation Route</strong><br/>
            <span>From: ${props.origin_name}</span><br/>
            <span>To: ${props.destination_name}</span><br/>
            <span>Vehicles: ${props.demand_vehicles} | Time: ${props.estimated_time_min} min</span>
          </div>
        `, { sticky: true, className: 'hud-map-tooltip' });
      }
    });
  }
};
