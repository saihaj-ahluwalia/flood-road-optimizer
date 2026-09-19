/**
 * AquaRoute AI - Road Criticality Layer Module
 * Renders color-coded road segments with Tier badges and click-to-inspect handlers.
 */

window.RoadsLayer = {
  create: function(roadsGeoJson, onRoadClick) {
    if (!roadsGeoJson || !roadsGeoJson.features) return L.layerGroup();

    return L.geoJSON(roadsGeoJson, {
      style: function(feature) {
        const props = feature.properties || {};
        const score = props.criticality_score || 0;
        let color = '#10b981';
        let weight = 3.5;
        let dashArray = null;

        if (score >= 75) {
          color = '#ef4444';
          weight = 6;
        } else if (score >= 55) {
          color = '#f97316';
          weight = 5;
        } else if (score >= 35) {
          color = '#eab308';
          weight = 4;
        }

        if (props.flood_depth_m >= 0.50) {
          dashArray = '6, 6'; // Impassable submerged road
        }

        return {
          color: color,
          weight: weight,
          opacity: 0.85,
          dashArray: dashArray,
          lineCap: 'round',
          lineJoin: 'round'
        };
      },
      onEachFeature: function(feature, layer) {
        const props = feature.properties || {};

        // Hover Tooltip
        layer.bindTooltip(`
          <div style="font-family:sans-serif; font-size:12px; padding:2px;">
            <strong>🛣️ ${props.name}</strong><br/>
            <span style="color:${props.tier_color}; font-weight:bold;">RCS: ${props.criticality_score}</span> (${props.tier})<br/>
            <span>Water: ${props.flood_depth_m}m | Flow: ${props.flow_volume} veh</span>
          </div>
        `, { sticky: true, className: 'hud-map-tooltip' });

        // Click Handler
        layer.on('click', function() {
          if (onRoadClick) {
            onRoadClick(props);
          }
        });

        // Hover highlight
        layer.on('mouseover', function() {
          layer.setStyle({ opacity: 1.0, weight: layer.options.weight + 2.5 });
        });
        layer.on('mouseout', function() {
          layer.setStyle({ opacity: 0.85, weight: layer.options.weight - 2.5 });
        });
      }
    });
  }
};
