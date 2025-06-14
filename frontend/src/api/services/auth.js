import { api } from "./client";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

export const authService = {
  login() {
    window.location.href = `${apiBaseUrl}/auth/oauth/login`;
  },

  async localLogin(username, password) {
    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);

    const response = await api.post("/auth/login", formData);
    return response.data;
  },

  logout() {
    return api.post("/auth/logout");
  },
};
