/**
 * AquaRoute AI - Hazard Layer Module
 * Renders flood inundation depth grid cells with opacity and tooltips.
 */

window.HazardLayer = {
  create: function(hazardGeoJson) {
    if (!hazardGeoJson || !hazardGeoJson.features) return L.layerGroup();

    return L.geoJSON(hazardGeoJson, {
      style: function(feature) {
        const props = feature.properties || {};
        return {
          fillColor: props.color || '#0284c7',
          weight: 0.5,
          opacity: 0.2,
          color: '#ffffff',
          fillOpacity: props.opacity || 0.45
        };
      },
      onEachFeature: function(feature, layer) {
        const props = feature.properties || {};
        const depth = props.depth_m ? props.depth_m.toFixed(2) : '0.00';
        const elev = props.elevation_m ? props.elevation_m.toFixed(1) : '5.0';

        layer.bindTooltip(`
          <div style="font-family:sans-serif; font-size:12px; padding:2px;">
            <strong style="color:#38bdf8;">🌊 Flood Depth: ${depth} m</strong><br/>
            <span>Elevation: ${elev} m ASL</span><br/>
            <span style="text-transform:capitalize; color:#9ca3af;">Severity: ${props.severity || 'Moderate'}</span>
          </div>
        `, { sticky: true, className: 'hud-map-tooltip' });
      }
    });
  }
};
