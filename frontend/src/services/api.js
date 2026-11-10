
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
});

// Automatically attach JWT to API requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

// Generate and save an AI itinerary
export async function generateItinerary(tripId) {
  const response = await api.post(`/trips/${tripId}/generate-itinerary`);

  return response.data;
}

// Retrieve an existing saved itinerary
export async function getItinerary(tripId) {
  const response = await api.get(`/trips/${tripId}/itinerary`);

  return response.data;
}

export default api;
