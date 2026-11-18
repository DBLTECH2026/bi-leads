// Dónde está la API (el servidor Spring Boot).
// En local el HTML corre en :8081 y la API en :8080 (como en el PDF del curso).
// En el VPS nginx sirve el HTML y reenvía /api a la API, así que basta la misma dirección.
window.BI_CONFIG = {
  API_BASE: location.port === "8081" ? "http://localhost:8080" : "",
};
