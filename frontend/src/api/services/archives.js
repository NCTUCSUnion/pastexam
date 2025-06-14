import { api } from "./client";

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

  deleteArchive(courseId, archiveId) {
    return api.delete(`/courses/${courseId}/archives/${archiveId}`);
  },

  updateArchive(courseId, archiveId, data) {
    const formData = new FormData();
    Object.entries(data).forEach(([key, value]) => {
      formData.append(key, value);
    });
    return api.patch(`/courses/${courseId}/archives/${archiveId}`, formData);
  },

  updateArchiveCourse(courseId, archiveId, newCourseId) {
    return api.patch(`/courses/${courseId}/archives/${archiveId}/course`, {
      course_id: newCourseId,
    });
  },
};
