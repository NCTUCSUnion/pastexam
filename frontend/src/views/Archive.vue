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
                :options="examTypes"
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
                groupedExams.length ? groupedExams[0].year.toString() : ''
              "
            >
              <AccordionPanel
                v-for="group in groupedExams"
                :key="group.year"
                :value="group.year.toString()"
              >
                <AccordionHeader>{{ group.year }} 年</AccordionHeader>
                <AccordionContent>
                  <DataTable :value="group.list">
                    <Column header="類型" style="width: 15%">
                      <template #body="{ data }">
                        <Tag
                          :severity="
                            data.type === '期中考'
                              ? 'info'
                              : data.type === '期末考'
                              ? 'warning'
                              : 'secondary'
                          "
                          class="text-sm"
                        >
                          {{ data.type }}
                        </Tag>
                      </template>
                    </Column>
                    <Column
                      header="教授"
                      field="professor"
                      style="width: 20%"
                    ></Column>
                    <Column header="解答" style="width: 15%">
                      <template #body="{ data }">
                        <Tag
                          :severity="data.hasAnswers ? 'success' : 'warning'"
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
                            @click="previewExam(data)"
                            size="small"
                            severity="secondary"
                            label="預覽"
                          />
                          <Button
                            icon="pi pi-download"
                            @click="downloadExam(data)"
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
          <div v-else class="flex align-items-center justify-content-center">
            請從左側選單選擇科目
          </div>
        </div>

        <!-- Preview Dialog -->
        <Dialog
          v-model:visible="showPreview"
          :modal="true"
          :style="{ width: '90vw', height: '90vh' }"
          :maximizable="true"
        >
          <iframe
            v-if="selectedExam"
            :src="selectedExam.previewUrl"
            class="w-full h-full"
            frameborder="0"
          />
        </Dialog>

        <Dialog
          v-model:visible="showUploadDialog"
          modal
          header="上傳考古題"
          :style="{ width: '50vw' }"
        >
          <div class="flex flex-column gap-4">
            <div class="flex flex-column gap-2">
              <label>科目</label>
              <Select
                v-model="uploadForm.subject"
                :options="allSubjects"
                optionLabel="name"
                placeholder="選擇科目"
                class="w-full"
                filter
                editable
              />
            </div>
            <div class="flex flex-column gap-2">
              <label>教授</label>
              <Select
                v-model="uploadForm.professor"
                placeholder="輸入教授姓名"
                class="w-full"
                filter
                editable
              />
            </div>
            <div class="flex flex-column gap-2">
              <label>考試類型</label>
              <Select
                v-model="uploadForm.type"
                :options="[
                  { name: '期中考', value: '期中考' },
                  { name: '期末考', value: '期末考' },
                  { name: '小考', value: '小考' },
                ]"
                optionLabel="name"
                placeholder="選擇考試類型"
                class="w-full"
              />
            </div>
            <div class="flex align-items-center gap-2">
              <Checkbox v-model="uploadForm.hasAnswers" :binary="true" />
              <label>附解答</label>
            </div>
            <FileUpload
              mode="basic"
              accept="application/pdf"
              :maxFileSize="10000000"
              chooseLabel="選擇 PDF 檔案"
              class="w-full"
              @select="onFileSelect"
            />
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
import { courseService } from "../services/api";
import { useToast } from "primevue/usetoast";

const toast = useToast();

const exams = ref([]);
const loading = ref(true);
const filters = ref({
  year: "",
  professor: "",
  type: "",
  hasAnswers: false,
});

const showPreview = ref(false);
const selectedExam = ref(null);
const selectedSubject = ref(null);
const selectedCourse = ref(null);
const showUploadDialog = ref(false);
const uploadForm = ref({
  subject: null,
  professor: "",
  type: null,
  hasAnswers: false,
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

const years = ref([]);
const professors = ref([]);
const examTypes = ref([]);

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

const groupedExams = computed(() => {
  if (!exams.value) return [];

  const filteredExams = exams.value.filter((exam) => {
    if (filters.value.year && exam.year.toString() !== filters.value.year)
      return false;
    if (filters.value.professor && exam.professor !== filters.value.professor)
      return false;
    if (filters.value.type && exam.type !== filters.value.type) return false;
    if (filters.value.hasAnswers && !exam.hasAnswers) return false;
    return true;
  });

  const groups = {};
  filteredExams.forEach((exam) => {
    if (!groups[exam.year]) {
      groups[exam.year] = {
        year: exam.year,
        list: [],
      };
    }
    groups[exam.year].list.push(exam);
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
  fetchExams();
}

async function fetchExams() {
  try {
    loading.value = true;
    const response = await courseService.getCourseArchives(
      selectedCourse.value
    );
    exams.value = response.data.map((exam) => ({
      id: exam.id,
      year: exam.academic_year,
      type: exam.archive_type,
      professor: exam.professor,
      hasAnswers: exam.has_answers,
      subject: selectedSubject.value,
    }));

    const uniqueYears = new Set();
    const uniqueProfessors = new Set();
    const uniqueTypes = new Set();

    exams.value.forEach((exam) => {
      if (exam.year) uniqueYears.add(exam.year.toString());
      if (exam.professor) uniqueProfessors.add(exam.professor);
      if (exam.type) uniqueTypes.add(exam.type);
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

    examTypes.value = Array.from(uniqueTypes)
      .sort()
      .map((type) => ({
        name: type,
        code: type,
      }));
  } catch (error) {
    console.error("Error fetching exams:", error);
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

async function downloadExam(exam) {
  try {
    const response = await courseService.getArchiveDownloadUrl(
      selectedCourse.value,
      exam.id
    );
    window.open(response.data.download_url, "_blank");
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

async function previewExam(exam) {
  try {
    const response = await courseService.getArchiveDownloadUrl(
      selectedCourse.value,
      exam.id
    );
    selectedExam.value = {
      ...exam,
      previewUrl: response.data.preview_url,
    };
    showPreview.value = true;
  } catch (error) {
    console.error("Preview error:", error);
    toast.add({
      severity: "error",
      summary: "預覽失敗",
      detail: "無法取得預覽連結",
      life: 3000,
    });
  }
}

const handleUpload = async () => {
  try {
    const formData = new FormData();
    formData.append("file", uploadForm.value.file);
    formData.append("professor", uploadForm.value.professor);
    formData.append("exam_type", uploadForm.value.type.value);
    formData.append("has_answers", uploadForm.value.hasAnswers);

    await courseService.uploadArchive(selectedCourse.value, formData);

    toast.add({
      severity: "success",
      summary: "上傳成功",
      detail: "考題已成功上傳",
      life: 3000,
    });
    showUploadDialog.value = false;
    await fetchExams();
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

onMounted(async () => {
  await fetchCourses();
});
</script>

<style scoped></style>
