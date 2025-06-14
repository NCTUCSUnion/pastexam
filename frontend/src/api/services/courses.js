import { api } from "./client";

export const courseService = {
  listCourses() {
    return api.get("/courses");
  },

  getCourseArchives(courseId) {
    return api.get(`/courses/${courseId}/archives`);
  },

  getAllCourses() {
    return api.get("/courses/admin/courses");
  },

  createCourse(courseData) {
    return api.post("/courses/admin/courses", courseData);
  },

  updateCourse(courseId, courseData) {
    return api.put(`/courses/admin/courses/${courseId}`, courseData);
  },

  deleteCourse(courseId) {
    return api.delete(`/courses/admin/courses/${courseId}`);
  },
};
