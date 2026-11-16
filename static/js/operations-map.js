(function () {
  var node = document.getElementById("operations-map-data");
  var mapEl = document.getElementById("operations-map");
  if (!node || !mapEl || typeof L === "undefined") {
    return;
  }
  var payload;
  try {
    payload = JSON.parse(node.textContent);
  } catch (error) {
    return;
  }
  var stations = payload.stations || [];
  var incidents = payload.incidents || [];
  var origin = payload.origin;
  if (!stations.length && !incidents.length && !origin) {
    return;
  }
  var map = L.map(mapEl);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> (demo tiles; not a production usage agreement)',
  }).addTo(map);
  var bounds = [];
  var severityColor = {
    critical: "#b42318",
    high: "#d97706",
    medium: "#ca8a04",
    low: "#2563eb",
  };

  function bindDomPopup(layer, nodeContent) {
    layer.bindPopup(nodeContent);
  }

  stations.forEach(function (station) {
    var latlng = [station.latitude, station.longitude];
    bounds.push(latlng);
    var marker = L.marker(latlng).addTo(map);
    var wrap = document.createElement("div");
    var link = document.createElement("a");
    link.textContent = station.name + " (" + station.code + ")";
    if (station.url) {
      link.setAttribute("href", station.url);
    }
    wrap.appendChild(link);
    if (station.distance_label) {
      var distance = document.createElement("div");
      distance.textContent = station.distance_label;
      wrap.appendChild(distance);
    }
    bindDomPopup(marker, wrap);
  });

  incidents.forEach(function (incident) {
    var latlng = [incident.latitude, incident.longitude];
    bounds.push(latlng);
    var marker = L.circleMarker(latlng, {
      radius: 8,
      color: severityColor[incident.severity] || "#334155",
      fillOpacity: 0.85,
    }).addTo(map);
    var wrap = document.createElement("div");
    var link = document.createElement("a");
    link.textContent = incident.title;
    if (incident.url) {
      link.setAttribute("href", incident.url);
    }
    wrap.appendChild(link);
    var meta = document.createElement("div");
    meta.textContent =
      incident.severity_label + " · " + incident.station_name;
    wrap.appendChild(meta);
    bindDomPopup(marker, wrap);
  });

  if (origin) {
    var originLatLng = [origin.latitude, origin.longitude];
    bounds.push(originLatLng);
    L.circle(originLatLng, {
      radius: origin.radius_meters,
      color: "#0f766e",
      fillOpacity: 0.05,
    }).addTo(map);
    L.circleMarker(originLatLng, {
      radius: 5,
      color: "#0f766e",
      fillOpacity: 1,
    }).addTo(map);
  }

  if (bounds.length === 1) {
    map.setView(bounds[0], 12);
  } else if (bounds.length) {
    map.fitBounds(bounds, { padding: [24, 24] });
  } else {
    map.setView([51.1657, 10.4515], 6);
  }
})();
