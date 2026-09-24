let globeInstance = null;

function initGlobe() {
  globeInstance = Globe()(document.getElementById("globe-container"))
    .globeImageUrl("https://unpkg.com/three-globe/example/img/earth-dark.jpg")
    .backgroundColor("rgba(0,0,0,0)")
    .pointsData([])
    .pointLat("lat")
    .pointLng("lng")
    .pointColor(() => "#c9973e")
    .pointRadius(0.6)
    .pointAltitude(0.02)
    .pointLabel(d => `${d.city || ""} ${d.country || ""}`)
    .onPointClick(showLocationDetail);
}

function plotLocation(geo) {
  if (!globeInstance || !geo || geo.lat == null || geo.lon == null) return;
  const point = {
    lat: geo.lat,
    lng: geo.lon,
    city: geo.city,
    country: geo.country,
    isp: geo.isp,
    org: geo.org,
    timezone: geo.timezone,
  };
  globeInstance.pointsData([point]);
  globeInstance.pointOfView({ lat: geo.lat, lng: geo.lon, altitude: 1.6 }, 1500);
  showLocationDetail(point);
}

function showLocationDetail(d) {
  const el = document.getElementById("location-detail");
  el.classList.remove("hidden");
  el.innerHTML = `
    <strong>${d.city || "Unknown city"}, ${d.country || "Unknown country"}</strong><br>
    ISP: ${d.isp || "n/a"}<br>
    Org: ${d.org || "n/a"}<br>
    Timezone: ${d.timezone || "n/a"}
  `;
}

document.addEventListener("DOMContentLoaded", initGlobe);
