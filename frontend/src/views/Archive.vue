<template>
  <Toast position="bottom-right" />
  <ConfirmDialog />
  <div class="flex h-full code-background relative">
    <div
      class="w-[20vw] h-full border-r border-solid surface-border p-3 shrink-0"
    >
      <PanelMenu :model="menuItems" multiple class="w-full" />
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
            <Accordion :value="expandedPanels" multiple>
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
                          {{ archiveTypeConfig[data.type]?.name || data.type }}
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
            class="flex align-items-center justify-content-center mt-4"
          >
            請從左側選單選擇科目
          </div>
        </div>

        <PdfPreviewModal
          v-model:visible="showPreview"
          :previewUrl="selectedArchive?.previewUrl"
          :title="selectedArchive?.name || ''"
          :loading="previewLoading"
          :error="previewError"
          @hide="closePreview"
          @error="handlePreviewError"
        >
          <template #footer>
            <Button
              v-if="selectedArchive"
              label="下載"
              icon="pi pi-download"
              @click="downloadArchive(selectedArchive)"
              severity="success"
            />
          </template>
        </PdfPreviewModal>

        <PdfPreviewModal
          v-model:visible="showUploadPreview"
          :previewUrl="uploadPreviewUrl"
          :title="uploadForm.file ? uploadForm.file.name : ''"
          :loading="uploadPreviewLoading"
          :error="uploadPreviewError"
          @hide="closeUploadPreview"
          @error="handleUploadPreviewError"
        />

        <Dialog
          v-model:visible="showUploadDialog"
          :modal="true"
          :draggable="false"
          :dismissableMask="true"
          :closeOnEscape="true"
          header="上傳考古題"
          :style="{ width: '50vw' }"
        >
          <Stepper v-model:value="uploadStep" linear>
            <StepList>
              <Step value="1">選擇課程</Step>
              <Step value="2">考試資訊</Step>
              <Step value="3">上傳檔案</Step>
              <Step value="4">確認資訊</Step>
            </StepList>

            <StepPanels>
              <StepPanel v-slot="{ activateCallback }" value="1">
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
                    <label>科目名稱</label>
                    <Select
                      v-model="uploadForm.subject"
                      :options="availableSubjects"
                      optionLabel="name"
                      optionValue="name"
                      placeholder="選擇科目"
                      class="w-full"
                      :disabled="!uploadForm.category"
                      filter
                      editable
                    />
                  </div>

                  <div class="flex flex-column gap-2">
                    <label>教授</label>
                    <Select
                      v-model="uploadForm.professor"
                      :options="availableProfessors"
                      optionLabel="name"
                      optionValue="code"
                      placeholder="選擇教授"
                      class="w-full"
                      :disabled="!uploadForm.subject"
                      filter
                      editable
                    />
                  </div>
                </div>
                <div class="flex pt-6 justify-end">
                  <Button
                    label="下一步"
                    icon="pi pi-arrow-right"
                    iconPos="right"
                    @click="activateCallback('2')"
                    :disabled="!canGoToStep2"
                  />
                </div>
              </StepPanel>

              <StepPanel v-slot="{ activateCallback }" value="2">
                <div class="flex flex-column gap-4">
                  <div class="flex flex-column gap-2">
                    <label>年份</label>
                    <DatePicker
                      v-model="uploadForm.academicYear"
                      view="year"
                      dateFormat="yy"
                      :showIcon="true"
                      placeholder="選擇年份"
                      class="w-full"
                      :maxDate="new Date()"
                      :minDate="new Date(2000, 0, 1)"
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

                  <div class="flex flex-column gap-2">
                    <label for="filename-input">考試名稱</label>
                    <div class="relative w-full">
                      <InputText
                        id="filename-input"
                        v-model="uploadForm.filename"
                        placeholder="輸入考試名稱"
                        class="w-full pr-8"
                        :class="{
                          'p-invalid': uploadForm.filename && !isFilenameValid,
                        }"
                        :maxlength="30"
                        @input="validateFilename"
                      />
                      <i
                        v-if="isFilenameValid && uploadForm.filename"
                        class="pi pi-check text-green-500 absolute right-3 top-1/2 -mt-2"
                      />
                      <i
                        v-else-if="uploadForm.filename"
                        class="pi pi-times text-red-500 absolute right-3 top-1/2 -mt-2"
                      />
                    </div>
                    <small
                      v-if="uploadForm.filename && !isFilenameValid"
                      class="p-error"
                    >
                      名稱格式必須是小寫英文，如需加入數字需加在結尾（如：midterm1、final、quiz3）
                    </small>
                    <small v-else class="text-gray-500">
                      請輸入小寫英文，如需加入數字需加在結尾（如：midterm1、final、quiz3）
                    </small>
                  </div>

                  <div class="flex align-items-center gap-2">
                    <Checkbox v-model="uploadForm.hasAnswers" :binary="true" />
                    <label>附解答</label>
                  </div>
                </div>
                <div class="flex pt-6 justify-between">
                  <Button
                    label="上一步"
                    icon="pi pi-arrow-left"
                    severity="secondary"
                    @click="activateCallback('1')"
                  />
                  <Button
                    label="下一步"
                    icon="pi pi-arrow-right"
                    iconPos="right"
                    @click="activateCallback('3')"
                    :disabled="!canGoToStep3"
                  />
                </div>
              </StepPanel>

              <StepPanel v-slot="{ activateCallback }" value="3">
                <div class="flex flex-column gap-4">
                  <FileUpload
                    ref="fileUpload"
                    accept="application/pdf"
                    :maxFileSize="10 * 1024 * 1024"
                    class="w-full"
                    @select="onFileSelect"
                    :multiple="false"
                    :auto="false"
                  >
                    <template #header="{ chooseCallback }">
                      <div
                        class="flex justify-between items-center flex-1 gap-4"
                      >
                        <div class="flex gap-2">
                          <Button
                            @click="chooseCallback()"
                            icon="pi pi-file-pdf"
                            rounded
                            outlined
                            severity="secondary"
                            label="選擇檔案"
                          ></Button>
                        </div>
                        <div v-if="uploadForm.file" class="text-sm text-500">
                          {{ formatFileSize(uploadForm.file.size) }} / 10MB
                        </div>
                      </div>
                    </template>

                    <template #content="{ files, removeFileCallback }">
                      <div v-if="uploadForm.file" class="flex flex-col gap">
                        <div class="p-4 surface-50 border-1 border-round">
                          <div class="flex align-items-center gap-3">
                            <i class="pi pi-file-pdf text-2xl"></i>
                            <div class="flex-1">
                              <div
                                class="font-semibold text-overflow-ellipsis overflow-hidden"
                              >
                                {{ uploadForm.file.name }}
                              </div>
                              <div class="text-sm text-500">
                                {{ formatFileSize(uploadForm.file.size) }}
                              </div>
                            </div>
                            <Button
                              icon="pi pi-times"
                              @click="clearSelectedFile(removeFileCallback)"
                              outlined
                              rounded
                              severity="danger"
                              size="small"
                            />
                          </div>
                        </div>
                      </div>
                    </template>

                    <template #empty>
                      <div
                        v-if="!uploadForm.file"
                        class="flex align-items-center justify-content-center flex-column p-5 border-1 border-dashed border-round"
                      >
                        <i
                          class="pi pi-cloud-upload border-2 border-round p-5 text-4xl text-500 mb-3"
                        ></i>
                        <p class="m-0 text-600">將 PDF 檔案拖放至此處以上傳</p>
                        <p class="m-0 text-sm text-500 mt-2">
                          僅接受 PDF 檔案，檔案大小最大 10MB
                        </p>
                      </div>
                    </template>
                  </FileUpload>
                </div>
                <div class="flex pt-6 justify-between">
                  <Button
                    label="上一步"
                    icon="pi pi-arrow-left"
                    severity="secondary"
                    @click="activateCallback('2')"
                  />
                  <Button
                    label="下一步"
                    icon="pi pi-arrow-right"
                    iconPos="right"
                    @click="activateCallback('4')"
                    :disabled="!uploadForm.file"
                  />
                </div>
              </StepPanel>

              <StepPanel v-slot="{ activateCallback }" value="4">
                <div class="flex flex-column gap-4">
                  <div
                    class="flex flex-column gap-2 p-3 surface-ground border-round"
                  >
                    <div>
                      <strong>課程類別：</strong>
                      {{ getCategoryName(uploadForm.category) }}
                    </div>
                    <div>
                      <strong>科目名稱：</strong> {{ uploadForm.subject }}
                    </div>
                    <div>
                      <strong>授課教授：</strong> {{ uploadForm.professor }}
                    </div>
                    <div>
                      <strong>考試年份：</strong>
                      {{ uploadForm.academicYear?.getFullYear() }}
                    </div>
                    <div>
                      <strong>考試類型：</strong>
                      {{ getTypeName(uploadForm.type) }}
                    </div>
                    <div>
                      <strong>考試名稱：</strong> {{ uploadForm.filename }}
                    </div>
                    <div>
                      <strong>是否附解答：</strong>
                      {{ uploadForm.hasAnswers ? "是" : "否" }}
                    </div>
                  </div>
                </div>
                <div class="flex pt-6 justify-between">
                  <Button
                    label="上一步"
                    icon="pi pi-arrow-left"
                    severity="secondary"
                    @click="activateCallback('3')"
                  />
                  <div class="flex gap-2.5">
                    <Button
                      icon="pi pi-eye"
                      label="預覽"
                      severity="secondary"
                      @click="previewUploadFile"
                    />
                    <Button
                      label="上傳"
                      icon="pi pi-upload"
                      severity="success"
                      @click="handleUpload"
                      :loading="uploading"
                      :disabled="!canUpload"
                    />
                  </div>
                </div>
              </StepPanel>
            </StepPanels>
          </Stepper>
        </Dialog>

        <Dialog
          v-model:visible="showEditDialog"
          :modal="true"
          :draggable="false"
          :dismissableMask="true"
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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from "vue";
import { courseService, archiveService } from "../services/api";
import { useToast } from "primevue/usetoast";
import { useConfirm } from "primevue/useconfirm";
import PdfPreviewModal from "../components/PdfPreviewModal.vue";
import { getCurrentUser } from "../utils/auth";

const toast = useToast();
const confirm = useConfirm();

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
const showUploadPreview = ref(false);
const uploadPreviewUrl = ref("");
const uploadPreviewLoading = ref(false);
const uploadPreviewError = ref(false);

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

const uploadStep = ref("1");
const uploading = ref(false);

const canGoToStep2 = computed(() => {
  return (
    uploadForm.value.category &&
    uploadForm.value.subject &&
    uploadForm.value.professor
  );
});

const isFilenameValid = ref(false);

function validateFilename() {
  const regex = /^[a-z]+[0-9]*$/;
  isFilenameValid.value = regex.test(uploadForm.value.filename);
}

const canGoToStep3 = computed(() => {
  return (
    uploadForm.value.academicYear &&
    uploadForm.value.type &&
    uploadForm.value.filename &&
    isFilenameValid.value
  );
});

const canUpload = computed(() => {
  return (
    uploadForm.value.file &&
    uploadForm.value.category &&
    uploadForm.value.subject &&
    uploadForm.value.professor &&
    uploadForm.value.academicYear &&
    uploadForm.value.type &&
    uploadForm.value.filename
  );
});

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

function getTypeName(code) {
  const types = {
    midterm: "期中考",
    final: "期末考",
    quiz: "小考",
    other: "其他",
  };
  return types[code] || code;
}

function uploadWithProgress(url, file) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", url, true);
    xhr.setRequestHeader("Content-Type", file.type);

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) resolve();
      else reject(new Error("Upload failed"));
    };

    xhr.onerror = () => reject(new Error("Upload failed"));
    xhr.send(file);
  });
}

const fileUpload = ref(null);

const handleUpload = async () => {
  try {
    uploading.value = true;

    const formData = new FormData();
    formData.append("file", uploadForm.value.file);
    formData.append("subject", uploadForm.value.subject);
    formData.append("category", uploadForm.value.category);
    formData.append("professor", uploadForm.value.professor);
    formData.append("archive_type", uploadForm.value.type);
    formData.append("has_answers", uploadForm.value.hasAnswers);
    formData.append("filename", uploadForm.value.filename);
    const year = new Date(uploadForm.value.academicYear).getFullYear();
    formData.append("academic_year", year);

    const { data } = await archiveService.uploadArchive(formData);

    await uploadWithProgress(data.upload_url, uploadForm.value.file);

    if (fileUpload.value) {
      fileUpload.value.clear();
    }

    showUploadDialog.value = false;
    uploadForm.value = {
      category: null,
      subject: "",
      professor: "",
      filename: "",
      type: null,
      hasAnswers: false,
      academicYear: null,
      file: null,
    };
    uploadStep.value = "1";

    await fetchCourses();
    if (selectedCourse.value) {
      await fetchArchives();
    }

    toast.add({
      severity: "success",
      summary: "上傳成功",
      detail: "考古題已成功上傳",
      life: 3000,
    });
  } catch (error) {
    console.error("Upload error:", error);
    toast.add({
      severity: "error",
      summary: "上傳失敗",
      detail: "請稍後再試",
      life: 3000,
    });
  } finally {
    uploading.value = false;
  }
};

const onFileSelect = (event) => {
  const newFile = event.files[0];

  if (fileUpload.value) {
    fileUpload.value.clear();
  }
  uploadForm.value.file = null;

  nextTick(() => {
    uploadForm.value.file = newFile;
  });
};

const availableSubjects = computed(() => {
  if (!uploadForm.value.category) return [];

  const subjects = coursesList.value[uploadForm.value.category] || [];
  return subjects
    .map((course) => ({
      name: course.name,
      code: course.id,
    }))
    .sort((a, b) => a.name.localeCompare(b.name));
});

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
    archiveData.forEach((archive) => {
      if (archive.professor) uniqueProfessors.add(archive.professor);
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
      // expandedPanels.value = [newGroups[0].year.toString()];
      expandedPanels.value = newGroups
        .slice(0, 3)
        .map((group) => group.year.toString());
      // expandedPanels.value = newGroups.map((group) => group.year.toString());
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
  return isAdmin.value || archive.uploader_id === getCurrentUser()?.uid;
};

const canEditArchive = (archive) => {
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
    archiveData.forEach((archive) => {
      if (archive.professor) uniqueProfessors.add(archive.professor);
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

function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

function clearSelectedFile(removeFileCallback) {
  if (removeFileCallback) removeFileCallback(0);
  uploadForm.value.file = null;
  if (fileUpload.value) {
    fileUpload.value.clear();
  }
}

function previewUploadFile() {
  if (!uploadForm.value.file) return;

  uploadPreviewLoading.value = true;
  uploadPreviewError.value = false;

  try {
    const fileUrl = URL.createObjectURL(
      new Blob([uploadForm.value.file], { type: "application/pdf" })
    );
    uploadPreviewUrl.value = fileUrl;
    showUploadPreview.value = true;
  } catch (error) {
    console.error("Preview error:", error);
    uploadPreviewError.value = true;
    toast.add({
      severity: "error",
      summary: "預覽失敗",
      detail: "無法預覽檔案",
      life: 3000,
    });
  } finally {
    uploadPreviewLoading.value = false;
  }
}

function handleUploadPreviewError() {
  uploadPreviewError.value = true;
}

function closeUploadPreview() {
  showUploadPreview.value = false;
  if (uploadPreviewUrl.value) {
    URL.revokeObjectURL(uploadPreviewUrl.value);
    uploadPreviewUrl.value = "";
  }
  uploadPreviewError.value = false;
}
</script>

<style scoped>
.code-background {
  position: relative;
}

.code-background::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300" viewBox="0 0 300 300"><text x="20" y="30" font-family="monospace" font-size="10" fill="rgba(255,255,255,0.05)">{}</text><text x="170" y="80" font-family="monospace" font-size="10" fill="rgba(255,255,255,0.05)">for()</text><text x="60" y="150" font-family="monospace" font-size="10" fill="rgba(255,255,255,0.05)">if()</text><text x="200" y="200" font-family="monospace" font-size="10" fill="rgba(255,255,255,0.05)">while</text><text x="120" y="240" font-family="monospace" font-size="10" fill="rgba(255,255,255,0.05)">;</text><text x="40" y="100" font-family="monospace" font-size="10" fill="rgba(255,255,255,0.05)">==</text></svg>');
  animation: scrollBackground 120s linear infinite;
  pointer-events: none;
  z-index: 0;
}

@keyframes scrollBackground {
  from {
    background-position: 0 0;
  }
  to {
    background-position: 300% 300%;
  }
}

.card {
  position: relative;
  z-index: 1;
  background-color: var(--surface-card);
}

.surface-border {
  position: relative;
  z-index: 1;
  background-color: var(--surface-card);
}
</style>
