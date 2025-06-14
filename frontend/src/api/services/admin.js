import { api } from "./client";

export const getCourses = () => {
  return api.get("/courses/admin/courses");
};

export const createCourse = (courseData) => {
  return api.post("/courses/admin/courses", courseData);
};

export const updateCourse = (courseId, courseData) => {
  return api.put(`/courses/admin/courses/${courseId}`, courseData);
};

export const deleteCourse = (courseId) => {
  return api.delete(`/courses/admin/courses/${courseId}`);
};
export const getUsers = () => {
  return api.get("/users/admin/users");
};

export const createUser = (userData) => {
  return api.post("/users/admin/users", userData);
};

export const updateUser = (userId, userData) => {
  return api.put(`/users/admin/users/${userId}`, userData);
};

export const deleteUser = (userId) => {
  return api.delete(`/users/admin/users/${userId}`);
};
