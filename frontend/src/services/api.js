import axios from "axios";
import router from "../router";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

export const api = axios.create({
  baseURL: apiBaseUrl,
  withCredentials: true,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("authToken");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("authToken");

      if (router.currentRoute.value.path !== "/") {
        router.push("/");
      }
    }
    return Promise.reject(error);
  }
);

export const courseService = {
  listCourses() {
    return api.get("/courses");
  },

  getCourseArchives(courseId) {
    return api.get(`/courses/${courseId}/archives`);
  },
};

export const archiveService = {
  uploadArchive(formData) {
    return api.post("/archives/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },

  getArchiveUrl(courseId, archiveId) {
    return api.get(`/courses/${courseId}/archives/${archiveId}/url`);
  },
};
