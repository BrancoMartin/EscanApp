const API_BASE_URL = "http://10.0.2.2:8000";

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  const config = {
    headers: { "Content-Type": "application/json" },
    ...options,
  };

  const response = await fetch(url, config);
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Error en la solicitud");
  }

  return data;
}

export function getCategories() {
  return request("/api/categories");
}

export function getProducts() {
  return request("/api/products/");
}

export function getProductByBarcode(barcode) {
  return request(`/api/products/barcode/${encodeURIComponent(barcode)}`);
}

export function createProduct(barcode, name, price, description) {
  return request("/api/products/", {
    method: "POST",
    body: JSON.stringify({ barcode, name, price, description }),
  });
}

export function getPendingSale() {
  return request("/api/sales/pending");
}

export function scanProduct(barcode) {
  return getProductByBarcode(barcode);
}

export function closeSale(saleId) {
  return request(`/api/sales/${saleId}/close`, { method: "POST" });
}

export function cancelSale(saleId) {
  return request(`/api/sales/${saleId}`, { method: "DELETE" });
}

export function cancelItem(saleId, itemId) {
  return request(`/api/sales/${saleId}/items/${itemId}`, { method: "PUT" });
}

export function getSalesByDate(date) {
  return request(`/api/sales/date/${date}`);
}

export function sendAgentMessage(message, conversationHistory = [], context = {}) {
  return request("/api/agent/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      conversation_history: conversationHistory,
      context,
    }),
  });
}
