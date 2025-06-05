<template>
  <div class="flex h-full">
    <div class="w-80 h-full border-r border-solid surface-border p-3 shrink-0">
      <PanelMenu :model="menuItems" class="w-full" />
    </div>

    <div class="flex-1 h-full overflow-auto">
      <div class="card h-full flex flex-col">
        <Toolbar class="m-3">
          <template #start>
            <div class="flex flex-wrap gap-3">
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
              :value="
                groupedArchives.length ? groupedArchives[0].year.toString() : ''
              "
            >
              <AccordionPanel
                v-for="group in groupedArchives"
                :key="group.year"
                :value="group.year.toString()"
              >
                <AccordionHeader>{{ group.year }} 年</AccordionHeader>
                <AccordionContent>
                  <DataTable :value="group.list">
                    <Column header="類型" style="width: 10%">
                      <template #body="{ data }">
                        <Tag
                          :severity="
                            archiveTypeConfig[data.type]?.severity ||
                            'secondary'
                          "
                          class="text-sm"
                        >
                          {{ archiveTypeConfig[data.type]?.name || data.type }}
                        </Tag>
                      </template>
                    </Column>
                    <Column
                      header="教授"
                      field="professor"
                      style="width: 10%"
                    ></Column>
                    <Column
                      header="檔名"
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
                    <Column header="操作" style="width: 20%">
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
            class="flex align-items-center justify-content-center mt-4"
          >
            請從左側選單選擇科目
          </div>
        </div>

        <Dialog
          v-model:visible="showPreview"
          modal
          :style="{ width: '90vw', height: '90vh' }"
          :contentStyle="{ height: '80vh' }"
          :maximizable="true"
          :dismissableMask="true"
          :closeOnEscape="true"
          @hide="closePreview"
        >
          <template #header>
            <div class="flex align-items-center gap-2">
              <i class="pi pi-file-pdf text-2xl" />
              <span class="text-xl">{{ selectedArchive?.name }}</span>
            </div>
          </template>

          <div class="w-full h-full flex flex-column">
            <div
              v-if="previewLoading"
              class="flex-1 flex align-items-center justify-content-center"
            >
              <ProgressSpinner />
            </div>

            <div
              v-else-if="previewError"
              class="flex-1 flex flex-column align-items-center justify-content-center gap-4"
            >
              <i class="pi pi-exclamation-circle text-6xl text-red-500" />
              <div class="text-xl">無法載入預覽</div>
              <div class="text-sm text-gray-600">請嘗試下載檔案查看</div>
            </div>

            <div
              v-else-if="selectedArchive?.previewUrl"
              class="flex-1 relative"
            >
              <iframe
                :src="selectedArchive.previewUrl"
                class="absolute top-0 left-0 w-full h-full"
                frameborder="0"
                @load="handlePreviewLoad"
                @error="handlePreviewError"
                allow="fullscreen"
                referrerpolicy="no-referrer"
              />
            </div>
          </div>

          <template #footer>
            <Button
              v-if="selectedArchive"
              label="下載"
              icon="pi pi-download"
              @click="downloadArchive(selectedArchive)"
              severity="success"
            />
          </template>
        </Dialog>

        <Dialog
          v-model:visible="showUploadDialog"
          modal
          header="上傳考古題"
          :style="{ width: '50vw' }"
        >
          <div class="flex flex-column gap-4">
            <div class="flex flex-column gap-2">
              <label>類別</label>
              <Select
                v-model="uploadForm.category"
                :options="[
                  { name: '大一課程', value: 'freshman' },
                  { name: '大二課程', value: 'sophomore' },
                  { name: '大三課程', value: 'junior' },
                  { name: '大四課程', value: 'senior' },
                  { name: '研究所課程', value: 'graduate' },
                  { name: '跨領域課程', value: 'interdisciplinary' },
                ]"
                optionLabel="name"
                optionValue="value"
                placeholder="選擇課程類別"
                class="w-full"
              />
            </div>

            <div class="flex flex-column gap-2">
              <label>年份</label>
              <InputNumber
                v-model="uploadForm.academicYear"
                :min="2000"
                :max="9999"
                placeholder="請輸入年份（例：2023）"
                class="w-full"
              />
            </div>

            <div class="flex flex-column gap-2">
              <label>科目名稱</label>
              <InputText
                v-model="uploadForm.subject"
                placeholder="輸入科目名稱"
                class="w-full"
              />
            </div>

            <div class="flex flex-column gap-2">
              <label>教授</label>
              <InputText
                v-model="uploadForm.professor"
                placeholder="輸入教授姓名"
                class="w-full"
              />
            </div>

            <div class="flex flex-column gap-2">
              <label>檔案標題</label>
              <InputText
                v-model="uploadForm.filename"
                placeholder="輸入檔案標題（如：111學年度上學期期中考）"
                class="w-full"
              />
            </div>

            <div class="flex flex-column gap-2">
              <label>考試類型</label>
              <Select
                v-model="uploadForm.type"
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
              <Checkbox v-model="uploadForm.hasAnswers" :binary="true" />
              <label>附解答</label>
            </div>

            <div class="flex flex-column gap-2">
              <label>上傳檔案 (PDF)</label>
              <FileUpload
                mode="basic"
                accept="application/pdf"
                :maxFileSize="10000000"
                chooseLabel="選擇 PDF 檔案"
                class="w-full"
                @select="onFileSelect"
              />
            </div>
          </div>
          <template #footer>
            <Button
              label="取消"
              icon="pi pi-times"
              @click="showUploadDialog = false"
              text
            />
            <Button
              label="上傳"
              icon="pi pi-upload"
              @click="handleUpload"
              severity="success"
            />
          </template>
        </Dialog>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { courseService, archiveService } from "../services/api";
import { useToast } from "primevue/usetoast";

const toast = useToast();

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

const menuItems = computed(() => {
  const items = [];

  if (!coursesList.value) return items;

  items.push({
    label: "大一課程",
    icon: "pi pi-fw pi-book",
    items:
      coursesList.value?.freshman?.map((course) => ({
        label: course.name,
        command: () => filterBySubject(course),
      })) || [],
  });

  items.push({
    label: "大二課程",
    icon: "pi pi-fw pi-book",
    items:
      coursesList.value?.sophomore?.map((course) => ({
        label: course.name,
        command: () => filterBySubject(course),
      })) || [],
  });

  items.push({
    label: "大三課程",
    icon: "pi pi-fw pi-book",
    items:
      coursesList.value?.junior?.map((course) => ({
        label: course.name,
        command: () => filterBySubject(course),
      })) || [],
  });

  items.push({
    label: "大四課程",
    icon: "pi pi-fw pi-book",
    items:
      coursesList.value?.senior?.map((course) => ({
        label: course.name,
        command: () => filterBySubject(course),
      })) || [],
  });

  items.push({
    label: "研究所課程",
    icon: "pi pi-fw pi-graduation-cap",
    items:
      coursesList.value?.graduate?.map((course) => ({
        label: course.name,
        command: () => filterBySubject(course),
      })) || [],
  });

  items.push({
    label: "跨領域課程",
    icon: "pi pi-fw pi-globe",
    items:
      coursesList.value?.interdisciplinary?.map((course) => ({
        label: course.name,
        command: () => filterBySubject(course),
      })) || [],
  });

  items.push({
    label: "上傳考古題",
    icon: "pi pi-fw pi-cloud-upload",
    command: () => {
      showUploadDialog.value = true;
    },
  });

  return items;
});

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
  selectedSubject.value = course.name;
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

async function downloadArchive(archive) {
  try {
    const { data } = await archiveService.getArchiveUrl(
      selectedCourse.value,
      archive.id
    );
    window.open(data.download_url, "_blank");
  } catch (error) {
    console.error("Download error:", error);
    toast.add({
      severity: "error",
      summary: "下載失敗",
      detail: "無法取得下載連結",
      life: 3000,
    });
  }
}

const previewLoading = ref(false);
const previewError = ref(false);

async function previewArchive(archive) {
  try {
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

const handleUpload = async () => {
  try {
    if (
      !uploadForm.value.category ||
      !uploadForm.value.subject ||
      !uploadForm.value.professor ||
      !uploadForm.value.filename ||
      !uploadForm.value.type ||
      !uploadForm.value.academicYear ||
      !uploadForm.value.file
    ) {
      toast.add({
        severity: "error",
        summary: "資料不完整",
        detail: "請填寫所有必要欄位",
        life: 3000,
      });
      return;
    }

    const formData = new FormData();
    formData.append("file", uploadForm.value.file);
    formData.append("subject", uploadForm.value.subject);
    formData.append("category", uploadForm.value.category);
    formData.append("professor", uploadForm.value.professor);
    formData.append("archive_type", uploadForm.value.type);
    formData.append("has_answers", uploadForm.value.hasAnswers);
    formData.append("filename", uploadForm.value.filename);
    formData.append("academic_year", uploadForm.value.academicYear);

    // Upload file metadata and get presigned URL
    const { data } = await archiveService.uploadArchive(formData);

    // Upload file to MinIO using presigned URL
    await fetch(data.upload_url, {
      method: "PUT",
      body: uploadForm.value.file,
      headers: {
        "Content-Type": uploadForm.value.file.type,
      },
    });

    toast.add({
      severity: "success",
      summary: "上傳成功",
      detail: "考題已成功上傳",
      life: 3000,
    });

    showUploadDialog.value = false;
    uploadForm.value = {
      category: null,
      subject: "",
      professor: "",
      filename: "",
      type: null,
      hasAnswers: false,
      file: null,
    };

    if (selectedSubject.value === uploadForm.value.subject) {
      await fetchArchives();
    }
  } catch (error) {
    console.error("Upload error:", error);
    toast.add({
      severity: "error",
      summary: "上傳失敗",
      detail: "請稍後再試",
      life: 3000,
    });
  }
};

const onFileSelect = (event) => {
  uploadForm.value.file = event.files[0];
};

onMounted(async () => {
  await fetchCourses();
});
</script>

<style scoped></style>
