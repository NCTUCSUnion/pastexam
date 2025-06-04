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
            <Accordion value="0">
              <AccordionTab
                v-for="group in groupedExams"
                :key="group.year"
                :header="`${group.year} 年`"
                class="mb-2"
              >
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
              </AccordionTab>
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
              />
            </div>
            <div class="flex flex-column gap-2">
              <label>教授</label>
              <Select
                v-model="uploadForm.professor"
                placeholder="輸入教授姓名"
                class="w-full"
                filter
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
              chooseLabel="選擇PDF檔案"
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
import axios from "axios";

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
const showUploadDialog = ref(false);
const uploadForm = ref({
  subject: null,
  professor: "",
  type: null,
  hasAnswers: false,
  file: null,
});

const menuItems = ref([
  {
    label: "大學部課程",
    icon: "pi pi-fw pi-book",
    items: [
      {
        label: "一年級",
        items: [
          {
            label: "微積分",
            command: () => filterBySubject("微積分"),
          },
          {
            label: "線性代數",
            command: () => filterBySubject("線性代數"),
          },
        ],
      },
      {
        label: "二年級",
        items: [
          {
            label: "資料結構",
            command: () => filterBySubject("資料結構"),
          },
          {
            label: "離散數學",
            command: () => filterBySubject("離散數學"),
          },
        ],
      },
      {
        label: "三年級",
        items: [
          {
            label: "計算機組織",
            command: () => filterBySubject("計算機組織"),
          },
          {
            label: "演算法",
            command: () => filterBySubject("演算法"),
          },
        ],
      },
      {
        label: "四年級",
        items: [
          {
            label: "作業系統",
            command: () => filterBySubject("作業系統"),
          },
          {
            label: "網路",
            command: () => filterBySubject("網路"),
          },
        ],
      },
    ],
  },
  {
    label: "研究所課程",
    icon: "pi pi-fw pi-graduation-cap",
    items: [
      {
        label: "高等演算法",
        command: () => filterBySubject("高等演算法"),
      },
      {
        label: "高等作業系統",
        command: () => filterBySubject("高等作業系統"),
      },
    ],
  },
  {
    label: "跨領域課程",
    icon: "pi pi-fw pi-globe",
    items: [
      {
        label: "電路學",
        command: () => filterBySubject("電路學"),
      },
      {
        label: "電子學",
        command: () => filterBySubject("電子學"),
      },
    ],
  },
  {
    label: "研究所考古題",
    icon: "pi pi-fw pi-file",
    items: [
      {
        label: "線性代數",
        command: () => filterBySubject("線性代數"),
      },
      {
        label: "離散數學",
        command: () => filterBySubject("離散數學"),
      },
      {
        label: "資料結構",
        command: () => filterBySubject("資料結構"),
      },
      {
        label: "演算法",
        command: () => filterBySubject("演算法"),
      },
    ],
  },
  {
    label: "上傳考古題",
    icon: "pi pi-fw pi-cloud-upload",
    command: () => {
      showUploadDialog.value = true;
    },
  },
]);

function filterBySubject(subject) {
  selectedSubject.value = subject;
  filters.value.professor = "";
  filters.value.year = "";
  filters.value.type = "";
}

async function fetchExams() {
  try {
    loading.value = true;

    exams.value = [
      {
        id: 1,
        year: 2025,
        type: "期中考",
        professor: "陳鍾平",
        hasAnswers: true,
        downloadUrl: `/api/download/2025正規mid1.pdf`,
        previewUrl: `/api/preview/2025正規mid1.pdf`,
        subject: "正規語言",
      },
      {
        id: 2,
        year: 2023,
        type: "期末考",
        professor: "陳鍾平",
        hasAnswers: false,
        downloadUrl: `/api/download/正規final_2023.pdf`,
        previewUrl: `/api/preview/正規final_2023.pdf`,
        subject: "正規語言",
      },
      {
        id: 3,
        year: 2024,
        type: "期中考",
        professor: "黃凱揚",
        hasAnswers: true,
        downloadUrl: `/api/download/algo_mid_2024.pdf`,
        previewUrl: `/api/preview/algo_mid_2024.pdf`,
        subject: "演算法",
      },
      {
        id: 4,
        year: 2024,
        type: "期末考",
        professor: "黃凱揚",
        hasAnswers: true,
        downloadUrl: `/api/download/algo_final_2024.pdf`,
        previewUrl: `/api/preview/algo_final_2024.pdf`,
        subject: "演算法",
      },
      {
        id: 5,
        year: 2023,
        type: "期中考",
        professor: "張嘉泰",
        hasAnswers: false,
        downloadUrl: `/api/download/algo_mid_2023.pdf`,
        previewUrl: `/api/preview/algo_mid_2023.pdf`,
        subject: "演算法",
      },
      {
        id: 6,
        year: 2023,
        type: "期末考",
        professor: "張嘉泰",
        hasAnswers: true,
        downloadUrl: `/api/download/algo_final_2023.pdf`,
        previewUrl: `/api/preview/algo_final_2023.pdf`,
        subject: "演算法",
      },
      {
        id: 7,
        year: 2025,
        type: "期中考",
        professor: "虞竹平",
        hasAnswers: true,
        downloadUrl: `/api/download/os_mid_2025.pdf`,
        previewUrl: `/api/preview/os_mid_2025.pdf`,
        subject: "作業系統",
      },
      {
        id: 8,
        year: 2024,
        type: "期末考",
        professor: "虞竹平",
        hasAnswers: false,
        downloadUrl: `/api/download/os_final_2024.pdf`,
        previewUrl: `/api/preview/os_final_2024.pdf`,
        subject: "作業系統",
      },
      {
        id: 9,
        year: 2022,
        type: "期中考",
        professor: "吳明璋",
        hasAnswers: true,
        downloadUrl: `/api/download/os_mid_2022.pdf`,
        previewUrl: `/api/preview/os_mid_2022.pdf`,
        subject: "作業系統",
      },
      {
        id: 10,
        year: 2022,
        type: "小考",
        professor: "吳明璋",
        hasAnswers: true,
        downloadUrl: `/api/download/os_quiz_2022.pdf`,
        previewUrl: `/api/preview/os_quiz_2022.pdf`,
        subject: "作業系統",
      },
      {
        id: 11,
        year: 2024,
        type: "期中考",
        professor: "李毅郎",
        hasAnswers: true,
        downloadUrl: `/api/download/dl_mid_2024.pdf`,
        previewUrl: `/api/preview/dl_mid_2024.pdf`,
        subject: "深度學習",
      },
      {
        id: 12,
        year: 2023,
        type: "期末考",
        professor: "謝旻錚",
        hasAnswers: false,
        downloadUrl: `/api/download/dl_final_2023.pdf`,
        previewUrl: `/api/preview/dl_final_2023.pdf`,
        subject: "深度學習",
      },
      {
        id: 13,
        year: 2025,
        type: "期中考",
        professor: "林彥宇",
        hasAnswers: true,
        downloadUrl: `/api/download/ml_mid_2025.pdf`,
        previewUrl: `/api/preview/ml_mid_2025.pdf`,
        subject: "機器學習",
      },
      {
        id: 14,
        year: 2024,
        type: "期末考",
        professor: "彭文志",
        hasAnswers: true,
        downloadUrl: `/api/download/ml_final_2024.pdf`,
        previewUrl: `/api/preview/ml_final_2024.pdf`,
        subject: "機器學習",
      },
      {
        id: 15,
        year: 2021,
        type: "期中考",
        professor: "黃胤僖",
        hasAnswers: false,
        downloadUrl: `/api/download/dsp_mid_2021.pdf`,
        previewUrl: `/api/preview/dsp_mid_2021.pdf`,
        subject: "數位訊號處理",
      },
      {
        id: 16,
        year: 2021,
        type: "期末考",
        professor: "張添烜",
        hasAnswers: true,
        downloadUrl: `/api/download/dsp_final_2021.pdf`,
        previewUrl: `/api/preview/dsp_final_2021.pdf`,
        subject: "數位訊號處理",
      },
      {
        id: 17,
        year: 2025,
        type: "期末考",
        professor: "范欽雄",
        hasAnswers: true,
        downloadUrl: `/api/download/2025正規final.pdf`,
        previewUrl: `/api/preview/2025正規final.pdf`,
        subject: "正規語言",
      },
      {
        id: 18,
        year: 2022,
        type: "期末考",
        professor: "陳鍾平",
        hasAnswers: false,
        downloadUrl: `/api/download/正規final_2022.pdf`,
        previewUrl: `/api/preview/正規final_2022.pdf`,
        subject: "正規語言",
      },
      {
        id: 19,
        year: 2024,
        type: "期中考",
        professor: "林彥宇",
        hasAnswers: true,
        downloadUrl: `/api/download/ml_mid_2025.pdf`,
        previewUrl: `/api/preview/ml_mid_2025.pdf`,
        subject: "機器學習",
      },
      {
        id: 20,
        year: 2023,
        type: "期中考",
        professor: "黃胤僖",
        hasAnswers: false,
        downloadUrl: `/api/download/dsp_mid_2021.pdf`,
        previewUrl: `/api/preview/dsp_mid_2021.pdf`,
        subject: "數位訊號處理",
      },
      {
        id: 21,
        year: 2024,
        type: "期中考",
        professor: "黃凱揚",
        hasAnswers: true,
        downloadUrl: `/api/download/algo_mid_2024.pdf`,
        previewUrl: `/api/preview/algo_mid_2024.pdf`,
        subject: "演算法",
      },
    ];
    loading.value = false;
  } catch (error) {
    console.error("Error fetching exams:", error);
  } finally {
    loading.value = false;
  }
}

const filteredExams = computed(() => {
  if (!selectedSubject.value) {
    return [];
  }

  let subjectExams = exams.value.filter(
    (exam) => exam.subject === selectedSubject.value
  );

  if (filters.value.year) {
    subjectExams = subjectExams.filter(
      (exam) => exam.year === parseInt(filters.value.year)
    );
  }
  if (filters.value.professor) {
    subjectExams = subjectExams.filter(
      (exam) => exam.professor === filters.value.professor
    );
  }
  if (filters.value.type) {
    subjectExams = subjectExams.filter(
      (exam) => exam.type === filters.value.type
    );
  }
  if (filters.value.hasAnswers) {
    subjectExams = subjectExams.filter((exam) => exam.hasAnswers);
  }

  return subjectExams;
});

const groupedExams = computed(() => {
  const temp = {};
  filteredExams.value.forEach((exam) => {
    if (!temp[exam.year]) {
      temp[exam.year] = [];
    }
    temp[exam.year].push(exam);
  });

  const result = Object.keys(temp)
    .map((yearStr) => ({
      year: Number(yearStr),
      list: temp[yearStr].sort((a, b) => {
        const typeOrder = { 期中考: 0, 期末考: 1, 小考: 2 };
        return typeOrder[a.type] - typeOrder[b.type];
      }),
    }))
    .sort((a, b) => b.year - a.year);

  return result;
});

const years = computed(() => {
  if (!selectedSubject.value) return [];
  const uniqueYears = [
    ...new Set(
      exams.value
        .filter((exam) => exam.subject === selectedSubject.value)
        .map((e) => e.year)
    ),
  ];
  return uniqueYears
    .sort((a, b) => b - a)
    .map((year) => ({ name: year.toString(), code: year.toString() }));
});

const professors = computed(() => {
  if (!selectedSubject.value) return [];
  const uniqueProfessors = [
    ...new Set(
      exams.value
        .filter((exam) => exam.subject === selectedSubject.value)
        .map((e) => e.professor)
    ),
  ];
  return uniqueProfessors.sort().map((prof) => ({ name: prof, code: prof }));
});

const examTypes = computed(() => {
  if (!selectedSubject.value) return [];
  const uniqueTypes = [
    ...new Set(
      exams.value
        .filter((exam) => exam.subject === selectedSubject.value)
        .map((e) => e.type)
    ),
  ];
  return uniqueTypes.sort().map((type) => ({ name: type, code: type }));
});

function downloadExam(exam) {
  window.open(exam.downloadUrl, "_blank");
}

function previewExam(exam) {
  selectedExam.value = exam;
  showPreview.value = true;
}

const allSubjects = computed(() => {
  const subjects = [];
  menuItems.value.forEach((category) => {
    if (category.items) {
      category.items.forEach((grade) => {
        if (grade.items) {
          grade.items.forEach((subject) => {
            subjects.push({ name: subject.label, value: subject.label });
          });
        } else {
          subjects.push({ name: grade.label, value: grade.label });
        }
      });
    }
  });
  return [...new Set(subjects)];
});

const onFileSelect = (event) => {
  uploadForm.value.file = event.files[0];
};

const handleUpload = async () => {
  try {
    const formData = new FormData();
    formData.append("file", uploadForm.value.file);
    formData.append("subject", uploadForm.value.subject.value);
    formData.append("professor", uploadForm.value.professor);
    formData.append("type", uploadForm.value.type.value);
    formData.append("hasAnswers", uploadForm.value.hasAnswers);

    await axios.post("/api/upload-exam", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });

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

onMounted(() => {
  fetchExams();
});
</script>

<style scoped></style>
