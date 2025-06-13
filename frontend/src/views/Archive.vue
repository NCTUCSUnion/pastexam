<template>
  <div class="h-full" ref="archiveView" @toggle-sidebar="toggleSidebar">
    <div class="flex h-full relative">
      <div class="sidebar" :class="{ collapsed: !sidebarVisible }">
        <div class="flex flex-column gap-3 p-3">
          <div class="relative w-full">
            <i class="pi pi-search absolute left-4 top-1/2 -mt-2 text-500"></i>
            <InputText
              v-model="searchQuery"
              placeholder="搜尋課程"
              class="w-full pl-6"
            />
          </div>
          <div v-if="searchQuery" class="search-results">
            <div
              v-if="filteredCategories.length === 0"
              class="p-3 text-center text-500"
            >
              <i class="pi pi-search text-2xl mb-2"></i>
              <div>查無搜尋結果</div>
            </div>
            <div
              v-for="category in filteredCategories"
              :key="category.label"
              class="mb-2"
            >
              <div class="text-sm mb-1" style="color: var(--text-secondary)">
                {{ category.label }}
              </div>
              <div class="flex flex-col gap-1">
                <Button
                  v-for="course in category.items"
                  :key="course.label"
                  class="p-button-text search-result-btn text-color"
                  @click="
                    filterBySubject({ label: course.label, id: course.id })
                  "
                >
                  <span class="ellipsis">{{ course.label }}</span>
                </Button>
              </div>
            </div>
          </div>
          <PanelMenu v-else :model="menuItems" multiple class="w-full" />
        </div>
      </div>
      <div class="main-content flex-1 h-full overflow-auto">
        <div class="card h-full flex flex-col">
          <div
            v-if="selectedSubject"
            class="p-3 border-bottom-1 surface-border"
          >
            <div class="flex align-items-center gap-2">
              <Tag severity="secondary" class="text-sm">
                {{ getCategoryTag(getCategoryName(getCurrentCategory)) }}
              </Tag>
              <span class="text-xl font-medium">{{ selectedSubject }}</span>
            </div>
          </div>
          <Toolbar v-if="selectedSubject" class="m-3">
            <template #start>
              <div class="flex flex-wrap gap-3 w-full">
                <Select
                  v-model="filters.year"
                  :options="years"
                  optionLabel="name"
                  optionValue="code"
                  placeholder="選擇年份"
                  class="w-full md:w-14rem"
                  showClear
                  filter
                />
                <Select
                  v-model="filters.professor"
                  :options="professors"
                  optionLabel="name"
                  optionValue="code"
                  placeholder="選擇教授"
                  class="w-full md:w-14rem"
                  showClear
                  filter
                />
                <Select
                  v-model="filters.type"
                  :options="archiveTypes"
                  optionLabel="name"
                  optionValue="code"
                  placeholder="選擇類型"
                  class="w-full md:w-14rem"
                  showClear
                />
                <div class="flex align-items-center">
                  <Checkbox v-model="filters.hasAnswers" :binary="true" />
                  <label class="ml-2">附解答</label>
                </div>
              </div>
            </template>
          </Toolbar>

          <ProgressSpinner
            v-if="loading"
            class="w-full flex justify-content-center mt-4"
            strokeWidth="4"
          />

          <div v-else>
            <div v-if="selectedSubject">
              <Accordion
                :value="expandedPanels"
                multiple
                class="max-w-[calc(100%-2rem)] mx-auto"
              >
                <AccordionPanel
                  v-for="group in groupedArchives"
                  :key="group.year"
                  :value="group.year.toString()"
                >
                  <AccordionHeader>{{ group.year }} 年</AccordionHeader>
                  <AccordionContent>
                    <DataTable :value="group.list">
                      <Column
                        header="教授"
                        field="professor"
                        style="width: 10%"
                      ></Column>
                      <Column header="類型" style="width: 10%">
                        <template #body="{ data }">
                          <Tag
                            :severity="
                              archiveTypeConfig[data.type]?.severity ||
                              'secondary'
                            "
                            class="text-sm"
                          >
                            {{
                              archiveTypeConfig[data.type]?.name || data.type
                            }}
                          </Tag>
                        </template>
                      </Column>
                      <Column
                        header="考試名稱"
                        field="name"
                        style="width: 15%"
                      ></Column>
                      <Column header="解答" style="width: 10%">
                        <template #body="{ data }">
                          <Tag
                            :severity="data.hasAnswers ? 'info' : 'secondary'"
                            class="text-sm"
                          >
                            {{ data.hasAnswers ? "附解答" : "僅題目" }}
                          </Tag>
                        </template>
                      </Column>
                      <Column header="操作" style="width: 30%">
                        <template #body="{ data }">
                          <div class="flex gap-2.5">
                            <Button
                              icon="pi pi-eye"
                              @click="previewArchive(data)"
                              size="small"
                              severity="secondary"
                              label="預覽"
                            />
                            <Button
                              icon="pi pi-download"
                              @click="downloadArchive(data)"
                              size="small"
                              severity="success"
                              label="下載"
                              :loading="downloadingId === data.id"
                            />
                            <Button
                              v-if="canEditArchive(data)"
                              icon="pi pi-pencil"
                              @click="openEditDialog(data)"
                              size="small"
                              severity="warning"
                              label="編輯"
                            />
                            <Button
                              v-if="canDeleteArchive(data)"
                              icon="pi pi-trash"
                              @click="confirmDelete(data)"
                              size="small"
                              severity="danger"
                              label="刪除"
                            />
                          </div>
                        </template>
                      </Column>
                    </DataTable>
                  </AccordionContent>
                </AccordionPanel>
              </Accordion>
            </div>
            <div
              v-else
              class="flex flex-column align-items-center justify-content-center h-full"
              style="min-height: calc(100vh - 200px)"
            >
              <i
                class="pi pi-book text-6xl"
                style="color: var(--text-secondary)"
              ></i>
              <div
                class="text-xl font-medium mt-4"
                style="color: var(--text-secondary)"
              >
                請從左側選單選擇科目
              </div>
              <div class="text-sm mt-2" style="color: var(--text-secondary)">
                選擇課程後即可瀏覽相關考古題
              </div>
            </div>
          </div>

          <PdfPreviewModal
            :visible="showPreview"
            @update:visible="showPreview = $event"
            :previewUrl="selectedArchive?.previewUrl"
            :title="selectedArchive?.name || ''"
            :loading="previewLoading"
            :error="previewError"
            @hide="closePreview"
            @error="handlePreviewError"
            @download="handlePreviewDownload"
          />

          <UploadArchiveDialog
            v-model="showUploadDialog"
            :coursesList="coursesList"
            @upload-success="handleUploadSuccess"
          />

          <Dialog
            :visible="showEditDialog"
            @update:visible="showEditDialog = $event"
            :modal="true"
            :draggable="false"
            :closeOnEscape="true"
            header="編輯考古題資訊"
            :style="{ width: '50vw' }"
          >
            <div class="flex flex-column gap-4">
              <div class="flex flex-column gap-2">
                <label>考古題名稱</label>
                <InputText
                  v-model="editForm.name"
                  placeholder="輸入考古題名稱"
                  class="w-full"
                />
              </div>

              <div class="flex flex-column gap-2">
                <label>教授</label>
                <Select
                  v-model="editForm.professor"
                  :options="availableProfessors"
                  optionLabel="name"
                  optionValue="code"
                  placeholder="選擇教授"
                  class="w-full"
                  filter
                  editable
                />
              </div>

              <div class="flex flex-column gap-2">
                <label>考試類型</label>
                <Select
                  v-model="editForm.type"
                  :options="[
                    { name: '期中考', value: 'midterm' },
                    { name: '期末考', value: 'final' },
                    { name: '小考', value: 'quiz' },
                    { name: '其他', value: 'other' },
                  ]"
                  optionLabel="name"
                  optionValue="value"
                  placeholder="選擇考試類型"
                  class="w-full"
                />
              </div>

              <div class="flex align-items-center gap-2">
                <Checkbox v-model="editForm.hasAnswers" :binary="true" />
                <label>附解答</label>
              </div>
            </div>
            <div class="flex pt-6 justify-end gap-2">
              <Button
                label="取消"
                icon="pi pi-times"
                severity="secondary"
                @click="showEditDialog = false"
              />
              <Button
                label="儲存"
                icon="pi pi-check"
                severity="success"
                @click="handleEdit"
              />
            </div>
          </Dialog>
        </div>
      </div>

      <Button
        icon="pi pi-cloud-upload"
        label="上傳考古題"
        severity="success"
        rounded
        class="fixed right-4 bottom-4 z-5"
        @click="showUploadDialog = true"
      />
    </div>
  </div>
</template>

<script setup>
defineOptions({
  name: "ArchiveView",
});

import { ref, computed, onMounted, watch, inject } from "vue";
import { courseService, archiveService } from "../services/api";
import PdfPreviewModal from "../components/PdfPreviewModal.vue";
import UploadArchiveDialog from "../components/UploadArchiveDialog.vue";
import { getCurrentUser } from "../utils/auth";
import { useTheme } from "../utils/useTheme";

const toast = inject("toast");
const confirm = inject("confirm");

const { isDarkTheme } = useTheme();
const sidebarVisible = inject("sidebarVisible");

const archives = ref([]);
const loading = ref(true);
const filters = ref({
  year: "",
  professor: "",
  type: "",
  hasAnswers: false,
});

const showPreview = ref(false);
const selectedArchive = ref(null);
const selectedSubject = ref(null);
const selectedCourse = ref(null);
const showUploadDialog = ref(false);
const uploadForm = ref({
  category: null,
  subject: "",
  professor: "",
  filename: "",
  type: null,
  hasAnswers: false,
  academicYear: null,
  file: null,
});

const uploadFormProfessors = ref([]);
const expandedPanels = ref([]);

const coursesList = ref({
  freshman: [],
  sophomore: [],
  junior: [],
  senior: [],
  graduate: [],
  interdisciplinary: [],
});

const archiveTypeConfig = {
  midterm: {
    name: "期中考",
    severity: "secondary",
  },
  final: {
    name: "期末考",
    severity: "secondary",
  },
  quiz: {
    name: "小考",
    severity: "secondary",
  },
  other: {
    name: "其他",
    severity: "secondary",
  },
};

const years = ref([]);
const professors = ref([]);
const archiveTypes = ref([]);

const searchQuery = ref("");

const menuItems = computed(() => {
  const items = [];

  if (!coursesList.value) return items;

  items.push({
    label: "大一課程",
    icon: "pi pi-fw pi-book",
    items:
      coursesList.value?.freshman
        ?.map((course) => ({
          label: course.name,
          command: () => filterBySubject({ label: course.name, id: course.id }),
        }))
        .sort((a, b) => a.label.localeCompare(b.label)) || [],
  });

  items.push({
    label: "大二課程",
    icon: "pi pi-fw pi-book",
    items:
      coursesList.value?.sophomore
        ?.map((course) => ({
          label: course.name,
          command: () => filterBySubject({ label: course.name, id: course.id }),
        }))
        .sort((a, b) => a.label.localeCompare(b.label)) || [],
  });

  items.push({
    label: "大三課程",
    icon: "pi pi-fw pi-book",
    items:
      coursesList.value?.junior
        ?.map((course) => ({
          label: course.name,
          command: () => filterBySubject({ label: course.name, id: course.id }),
        }))
        .sort((a, b) => a.label.localeCompare(b.label)) || [],
  });

  items.push({
    label: "大四課程",
    icon: "pi pi-fw pi-book",
    items:
      coursesList.value?.senior
        ?.map((course) => ({
          label: course.name,
          command: () => filterBySubject({ label: course.name, id: course.id }),
        }))
        .sort((a, b) => a.label.localeCompare(b.label)) || [],
  });

  items.push({
    label: "研究所課程",
    icon: "pi pi-fw pi-graduation-cap",
    items:
      coursesList.value?.graduate
        ?.map((course) => ({
          label: course.name,
          command: () => filterBySubject({ label: course.name, id: course.id }),
        }))
        .sort((a, b) => a.label.localeCompare(b.label)) || [],
  });

  items.push({
    label: "跨領域課程",
    icon: "pi pi-fw pi-globe",
    items:
      coursesList.value?.interdisciplinary
        ?.map((course) => ({
          label: course.name,
          command: () => filterBySubject({ label: course.name, id: course.id }),
        }))
        .sort((a, b) => a.label.localeCompare(b.label)) || [],
  });

  return items;
});

const filteredCategories = computed(() => {
  if (!searchQuery.value) {
    return [];
  }

  const query = searchQuery.value.toLowerCase();
  const filtered = [];

  menuItems.value.forEach((category) => {
    const filteredItems = category.items.filter((item) =>
      item.label.toLowerCase().includes(query)
    );

    if (filteredItems.length > 0) {
      filtered.push({
        ...category,
        items: filteredItems
          .map((item) => {
            const course = coursesList.value[
              getCategoryKey(category.label)
            ].find((c) => c.name === item.label);
            return {
              label: item.label,
              id: course?.id,
            };
          })
          .sort((a, b) => a.label.localeCompare(b.label)),
      });
    }
  });

  return filtered;
});

function getCategoryKey(categoryLabel) {
  const categoryMap = {
    大一課程: "freshman",
    大二課程: "sophomore",
    大三課程: "junior",
    大四課程: "senior",
    研究所課程: "graduate",
    跨領域課程: "interdisciplinary",
  };
  return categoryMap[categoryLabel] || "";
}

const groupedArchives = computed(() => {
  if (!archives.value) return [];

  const filteredArchives = archives.value.filter((archive) => {
    if (filters.value.year && archive.year.toString() !== filters.value.year)
      return false;
    if (
      filters.value.professor &&
      archive.professor !== filters.value.professor
    )
      return false;
    if (filters.value.type && archive.type !== filters.value.type) return false;
    if (filters.value.hasAnswers && !archive.hasAnswers) return false;
    return true;
  });

  const groups = {};
  filteredArchives.forEach((archive) => {
    if (!groups[archive.year]) {
      groups[archive.year] = {
        year: archive.year,
        list: [],
      };
    }
    groups[archive.year].list.push(archive);
  });

  return Object.values(groups).sort((a, b) => b.year - a.year);
});

async function fetchCourses() {
  try {
    loading.value = true;
    const response = await courseService.listCourses();
    coursesList.value = response.data;
  } catch (error) {
    console.error("Error fetching courses:", error);
    toast.add({
      severity: "error",
      summary: "載入失敗",
      detail: "無法載入課程資料",
      life: 3000,
    });
  } finally {
    loading.value = false;
  }
}

function filterBySubject(course) {
  if (!course || !course.id) return;
  selectedSubject.value = course.label;
  selectedCourse.value = course.id;
  filters.value.professor = "";
  filters.value.year = "";
  filters.value.type = "";
  fetchArchives();
}

async function fetchArchives() {
  try {
    loading.value = true;
    const response = await courseService.getCourseArchives(
      selectedCourse.value
    );
    archives.value = response.data.map((archive) => ({
      id: archive.id,
      year: archive.academic_year,
      name: archive.name,
      type: archive.archive_type,
      professor: archive.professor,
      hasAnswers: archive.has_answers,
      subject: selectedSubject.value,
      uploader_id: archive.uploader_id,
    }));

    const uniqueYears = new Set();
    const uniqueProfessors = new Set();
    const uniqueTypes = new Set();

    archives.value.forEach((archive) => {
      if (archive.year) uniqueYears.add(archive.year.toString());
      if (archive.professor) uniqueProfessors.add(archive.professor);
      if (archive.type) uniqueTypes.add(archive.type);
    });

    years.value = Array.from(uniqueYears)
      .sort((a, b) => b - a)
      .map((year) => ({
        name: year,
        code: year,
      }));

    professors.value = Array.from(uniqueProfessors)
      .sort()
      .map((professor) => ({
        name: professor,
        code: professor,
      }));

    archiveTypes.value = Array.from(uniqueTypes)
      .sort()
      .map((type) => ({
        name: archiveTypeConfig[type]?.name || type,
        code: type,
      }));
  } catch (error) {
    console.error("Error fetching archives:", error);
    toast.add({
      severity: "error",
      summary: "載入失敗",
      detail: "無法載入考古題資料",
      life: 3000,
    });
  } finally {
    loading.value = false;
  }
}

const downloadingId = ref(null);
const previewingId = ref(null);

async function downloadArchive(archive) {
  try {
    downloadingId.value = archive.id;
    const { data } = await archiveService.getArchiveUrl(
      selectedCourse.value,
      archive.id
    );

    const response = await fetch(data.download_url);
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;

    const fileName = `${archive.year}_${selectedSubject.value}_${archive.professor}_${archive.name}.pdf`;
    link.download = fileName;
    link.style.display = "none";

    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(url);
    link.remove();

    toast.add({
      severity: "success",
      summary: "下載成功",
      detail: `已下載 ${fileName}`,
      life: 3000,
    });
  } catch (error) {
    console.error("Download error:", error);
    toast.add({
      severity: "error",
      summary: "下載失敗",
      detail: "無法取得下載連結",
      life: 3000,
    });
  } finally {
    downloadingId.value = null;
  }
}

const previewLoading = ref(false);
const previewError = ref(false);

async function previewArchive(archive) {
  try {
    previewingId.value = archive.id;
    previewLoading.value = true;
    previewError.value = false;
    showPreview.value = true;

    const { data } = await archiveService.getArchiveUrl(
      selectedCourse.value,
      archive.id
    );

    selectedArchive.value = {
      ...archive,
      previewUrl: data.preview_url,
    };
  } catch (error) {
    console.error("Preview error:", error);
    previewError.value = true;
    toast.add({
      severity: "error",
      summary: "預覽失敗",
      detail: "無法取得預覽連結",
      life: 3000,
    });
  } finally {
    previewLoading.value = false;
    previewingId.value = null;
  }
}

function handlePreviewError() {
  previewError.value = true;
}

function closePreview() {
  showPreview.value = false;
  selectedArchive.value = null;
  previewError.value = false;
}

function getCategoryName(code) {
  const categories = {
    freshman: "大一課程",
    sophomore: "大二課程",
    junior: "大三課程",
    senior: "大四課程",
    graduate: "研究所課程",
    interdisciplinary: "跨領域課程",
  };
  return categories[code] || code;
}

const availableProfessors = computed(() => {
  return uploadFormProfessors.value;
});

async function fetchProfessorsForSubject(subject) {
  if (!subject) return;

  try {
    let courseId = null;
    const category = uploadForm.value.category;

    if (category && coursesList.value[category]) {
      const course = coursesList.value[category].find(
        (c) => c.name === subject
      );
      if (course) {
        courseId = course.id;
      }
    }

    if (!courseId) return;

    const response = await courseService.getCourseArchives(courseId);
    const archiveData = response.data;

    const uniqueProfessors = new Set();
    archiveData.forEach((item) => {
      if (item.professor) uniqueProfessors.add(item.professor);
    });

    uploadFormProfessors.value = Array.from(uniqueProfessors)
      .sort()
      .map((professor) => ({
        name: professor,
        code: professor,
      }));
  } catch (error) {
    console.error("Error fetching professors for subject:", error);
    uploadFormProfessors.value = [];
  }
}

watch(
  () => uploadForm.value.subject,
  (newSubject) => {
    uploadForm.value.professor = "";
    if (newSubject) {
      fetchProfessorsForSubject(newSubject);
    } else {
      uploadFormProfessors.value = [];
    }
  }
);

watch(
  () => uploadForm.value.category,
  () => {
    uploadForm.value.subject = "";
    uploadForm.value.professor = "";
  }
);

watch(
  () => groupedArchives.value,
  (newGroups) => {
    if (newGroups.length) {
      expandedPanels.value = newGroups
        .slice(0, 3)
        .map((group) => group.year.toString());
    }
  },
  { immediate: true }
);

const isAdmin = ref(false);
const showEditDialog = ref(false);
const editForm = ref({
  id: null,
  name: "",
  professor: "",
  type: "",
  hasAnswers: false,
});

const canDeleteArchive = (archive) => {
  const currentUser = getCurrentUser();
  if (!currentUser) return false;

  return (
    isAdmin.value ||
    (archive.uploader_id && archive.uploader_id === currentUser.id)
  );
};

const canEditArchive = () => {
  return isAdmin.value;
};

const confirmDelete = (archive) => {
  confirm.require({
    message: "確定要刪除此考古題嗎？",
    header: "確認刪除",
    icon: "pi pi-exclamation-triangle",
    accept: () => {
      deleteArchive(archive);
    },
  });
};

const deleteArchive = async (archive) => {
  try {
    await archiveService.deleteArchive(selectedCourse.value, archive.id);
    await fetchArchives();
    toast.add({
      severity: "success",
      summary: "刪除成功",
      detail: "考古題已成功刪除",
      life: 3000,
    });
  } catch (error) {
    console.error("Delete error:", error);
    toast.add({
      severity: "error",
      summary: "刪除失敗",
      detail: error.response?.data?.detail || "請稍後再試",
      life: 3000,
    });
  }
};

const openEditDialog = async (archive) => {
  try {
    const response = await courseService.getCourseArchives(
      selectedCourse.value
    );
    const archiveData = response.data;

    const uniqueProfessors = new Set();
    archiveData.forEach((item) => {
      if (item.professor) uniqueProfessors.add(item.professor);
    });

    uploadFormProfessors.value = Array.from(uniqueProfessors)
      .sort()
      .map((professor) => ({
        name: professor,
        code: professor,
      }));

    editForm.value = {
      id: archive.id,
      name: archive.name,
      professor: archive.professor,
      type: archive.type,
      hasAnswers: archive.hasAnswers,
    };

    showEditDialog.value = true;
  } catch (error) {
    console.error("Error fetching professors:", error);
    toast.add({
      severity: "error",
      summary: "載入失敗",
      detail: "無法載入教授清單",
      life: 3000,
    });
  }
};

const handleEdit = async () => {
  try {
    await archiveService.updateArchive(
      selectedCourse.value,
      editForm.value.id,
      {
        name: editForm.value.name,
        professor: editForm.value.professor,
        archive_type: editForm.value.type,
        has_answers: editForm.value.hasAnswers,
      }
    );
    await fetchArchives();
    showEditDialog.value = false;
    toast.add({
      severity: "success",
      summary: "更新成功",
      detail: "考古題資訊已更新",
      life: 3000,
    });
  } catch (error) {
    console.error("Update error:", error);
    toast.add({
      severity: "error",
      summary: "更新失敗",
      detail: error.response?.data?.detail || "請稍後再試",
      life: 3000,
    });
  }
};

onMounted(async () => {
  const user = getCurrentUser();
  isAdmin.value = user?.is_admin || false;
  await fetchCourses();
});

watch(isDarkTheme, () => {
  // Remove setBg call
});

async function handleUploadSuccess() {
  await fetchCourses();
  if (selectedCourse.value) {
    await fetchArchives();
  }
}

function getCategoryTag(categoryLabel) {
  const categoryMap = {
    大一課程: "大一",
    大二課程: "大二",
    大三課程: "大三",
    大四課程: "大四",
    研究所課程: "研究所",
    跨領域課程: "跨領域",
  };
  return categoryMap[categoryLabel] || categoryLabel;
}

function toggleSidebar() {
  sidebarVisible.value = !sidebarVisible.value;
}

async function handlePreviewDownload(onComplete) {
  if (!selectedArchive.value) return;

  try {
    const { data } = await archiveService.getArchiveUrl(
      selectedCourse.value,
      selectedArchive.value.id
    );

    const response = await fetch(data.download_url);
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;

    const fileName = `${selectedArchive.value.year}_${selectedSubject.value}_${selectedArchive.value.professor}_${selectedArchive.value.name}.pdf`;
    link.download = fileName;
    link.style.display = "none";

    document.body.appendChild(link);
    link.click();
    window.URL.revokeObjectURL(url);
    link.remove();

    toast.add({
      severity: "success",
      summary: "下載成功",
      detail: `已下載 ${fileName}`,
      life: 3000,
    });
  } catch (error) {
    console.error("Download error:", error);
    toast.add({
      severity: "error",
      summary: "下載失敗",
      detail: "無法取得下載連結",
      life: 3000,
    });
  } finally {
    onComplete();
  }
}

const getCurrentCategory = computed(() => {
  if (!selectedCourse.value) return "";

  for (const [category, courses] of Object.entries(coursesList.value)) {
    const course = courses.find((c) => c.id === selectedCourse.value);
    if (course) return category;
  }
  return "";
});
</script>

<style scoped>
.card {
  position: relative;
  z-index: 1;
  background-color: var(--bg-primary);
}

.surface-border {
  position: relative;
  z-index: 1;
  background-color: var(--bg-primary);
  border-color: var(--border-color);
}

:deep(.p-sidebar) {
  padding: 0;
  background-color: var(--bg-primary);
  z-index: 2;
  border-right: 1px solid var(--border-color);
}

:deep(.p-sidebar-header) {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-primary);
}

:deep(.p-sidebar-content) {
  padding: 1rem;
  background-color: var(--bg-primary);
}

:deep(.p-input-icon-left) {
  width: 100%;
}

:deep(.p-input-icon-left i) {
  left: 0.75rem;
}

:deep(.p-input-icon-left input) {
  padding-left: 2.5rem;
  background: var(--bg-primary);
  border-color: var(--border-color);
  color: var(--text-color);
}

:deep(.p-input-icon-left input:focus) {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 1px var(--primary-color);
}

:deep(.p-accordionheader),
:deep(.p-panelmenu-header-link),
:deep(.p-panelmenu-content),
:deep(.p-button),
:deep(.p-button-outlined),
:deep(.p-inputtext),
:deep(.p-dropdown),
:deep(.p-select),
:deep(.p-checkbox),
:deep(.p-checkbox-box),
:deep(.p-checkbox-icon),
:deep(.p-tag),
:deep(.p-toolbar),
:deep(.p-datatable),
:deep(.p-datatable-thead > tr > th),
:deep(.p-datatable-tbody > *),
:deep(.p-dialog),
:deep(.p-dialog-header),
:deep(.p-dialog-content),
:deep(.p-dialog-footer) {
  transition: none !important;
}

/* Keep only sidebar transition */
.sidebar {
  width: 20vw;
  min-width: 220px;
  max-width: 320px;
  background: var(--bg-primary);
  border-right: 1px solid var(--border-color);
  transition:
    width 0.2s ease-in-out,
    min-width 0.2s ease-in-out,
    max-width 0.2s ease-in-out;
  overflow: hidden;
  position: relative;
  z-index: 1;
  height: 100%;
}

.sidebar .flex-column {
  width: 100%;
  opacity: 1;
  white-space: nowrap;
}

.sidebar .search-results {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
  padding: 0.5rem;
}

.sidebar .search-results .flex-wrap {
  white-space: nowrap;
  overflow: hidden;
}

.sidebar .search-results .p-button {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sidebar.collapsed {
  width: 0;
  min-width: 0;
  max-width: 0;
  padding: 0;
  border-right: none;
}

.sidebar.collapsed .flex-column {
  opacity: 0;
  pointer-events: none;
}

.main-content {
  flex: 1 1 0%;
  min-width: 0;
  background: var(--bg-primary);
  height: 100%;
}

.ellipsis {
  display: inline-block;
  max-width: 90%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: middle;
}

.search-result-btn {
  width: 100%;
  justify-content: flex-start;
  text-align: left;
  padding: 0.5rem;
  border-radius: 4px;
}

.search-results .text-sm {
  font-size: 0.875rem;
}
</style>
