(function () {
  var node = document.getElementById("station-map-data");
  var mapEl = document.getElementById("station-map");
  if (!node || !mapEl || typeof L === "undefined") {
    return;
  }
  var markers;
  try {
    markers = JSON.parse(node.textContent);
  } catch (error) {
    return;
  }
  if (!markers || !markers.length) {
    return;
  }
  var map = L.map(mapEl);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "&copy; <a href=\"https://www.openstreetmap.org/copyright\">OpenStreetMap</a>",
  }).addTo(map);
  var bounds = [];
  markers.forEach(function (station) {
    var latlng = [station.latitude, station.longitude];
    bounds.push(latlng);
    var marker = L.marker(latlng).addTo(map);
    var link = document.createElement("a");
    link.textContent = station.name + " (" + station.code + ")";
    if (station.url) {
      link.setAttribute("href", station.url);
    }
    marker.bindPopup(link);
  });
  if (bounds.length === 1) {
    map.setView(bounds[0], 13);
  } else {
    map.fitBounds(bounds, { padding: [24, 24] });
  }
})();
