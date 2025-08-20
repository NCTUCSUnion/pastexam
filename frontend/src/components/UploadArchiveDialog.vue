<template>
  <div>
    <Dialog
      :visible="modelValue"
      @update:visible="$emit('update:modelValue', $event)"
      :modal="true"
      :draggable="false"
      :closeOnEscape="false"
      header="上傳考古題"
      :style="{ width: '700px', maxWidth: '90vw' }"
      :autoFocus="false"
    >
      <Stepper :value="uploadStep" @update:value="uploadStep = $event" linear>
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
                  v-model="form.category"
                  :options="[
                    { name: '大一課程', value: 'freshman' },
                    { name: '大二課程', value: 'sophomore' },
                    { name: '大三課程', value: 'junior' },
                    { name: '大四課程', value: 'senior' },
                    { name: '研究所課程', value: 'graduate' },
                    { name: '跨領域課程', value: 'interdisciplinary' },
                    { name: '通識課程', value: 'general' },
                  ]"
                  optionLabel="name"
                  optionValue="value"
                  placeholder="選擇課程類別"
                  class="w-full"
                />
              </div>

              <div class="flex flex-column gap-2">
                <label>科目</label>
                <AutoComplete
                  v-model="form.subject"
                  :suggestions="availableSubjects"
                  @complete="searchSubject"
                  @item-select="onSubjectSelect"
                  @focus="() => searchSubject({ query: '' })"
                  @click="() => searchSubject({ query: '' })"
                  optionLabel="name"
                  placeholder="搜尋或輸入科目名稱"
                  class="w-full"
                  :disabled="!form.category"
                  dropdown
                  completeOnFocus
                  :minLength="0"
                  autoHighlight="true"
                >
                  <template #item="{ item }">
                    <div>{{ item.name }}</div>
                  </template>
                </AutoComplete>
              </div>

              <div class="flex flex-column gap-2">
                <label>教授</label>
                <AutoComplete
                  :modelValue="form.professor"
                  @update:modelValue="(val) => (form.professor = val)"
                  :suggestions="availableProfessors"
                  @complete="searchProfessor"
                  @item-select="onProfessorSelect"
                  @focus="() => searchProfessor({ query: '' })"
                  @click="() => searchProfessor({ query: '' })"
                  optionLabel="name"
                  placeholder="搜尋或輸入教授名稱"
                  class="w-full"
                  :disabled="!form.subject"
                  dropdown
                  completeOnFocus
                  :minLength="0"
                  autoHighlight="true"
                >
                  <template #item="{ item }">
                    <div>{{ item.name }}</div>
                  </template>
                </AutoComplete>
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
                  v-model="form.academicYear"
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
                  v-model="form.type"
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
                    v-model="form.filename"
                    placeholder="輸入考試名稱"
                    class="w-full pr-8"
                    :class="{
                      'p-invalid': form.filename && !isFilenameValid,
                    }"
                    :maxlength="30"
                    @input="validateFilename"
                  />
                  <i
                    v-if="isFilenameValid && form.filename"
                    class="pi pi-check text-green-500 absolute right-3 top-1/2 -mt-2"
                  />
                  <i
                    v-else-if="form.filename"
                    class="pi pi-times text-red-500 absolute right-3 top-1/2 -mt-2"
                  />
                </div>
                <small v-if="form.filename && !isFilenameValid" class="p-error">
                  名稱格式必須是小寫英文，如需加入數字需加在結尾（如：midterm1、final、quiz3）
                </small>
                <small v-else class="text-gray-500">
                  請輸入小寫英文，如需加入數字需加在結尾（如：midterm1、final、quiz3）
                </small>
              </div>

              <div class="flex align-items-center gap-2">
                <Checkbox v-model="form.hasAnswers" :binary="true" />
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
                  <div class="flex justify-between items-center flex-1 gap-4">
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
                    <div v-if="form.file" class="text-sm text-500">
                      {{ formatFileSize(form.file.size) }} / 10MB
                    </div>
                  </div>
                </template>

                <template #content="{ removeFileCallback }">
                  <div v-if="form.file" class="flex flex-col gap">
                    <div class="p-4 surface-50 border-1 border-round">
                      <div class="flex align-items-center gap-3">
                        <i class="pi pi-file-pdf text-2xl"></i>
                        <div class="flex-1">
                          <div
                            class="font-semibold text-overflow-ellipsis overflow-hidden"
                          >
                            {{ form.file.name }}
                          </div>
                          <div class="text-sm text-500">
                            {{ formatFileSize(form.file.size) }}
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
                    v-if="!form.file"
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
                :disabled="!form.file"
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
                  {{ getCategoryName(form.category) }}
                </div>
                <div>
                  <strong>科目名稱：</strong>
                  {{ form.subject || "" }}
                </div>
                <div><strong>授課教授：</strong> {{ form.professor }}</div>
                <div>
                  <strong>考試年份：</strong>
                  {{ form.academicYear?.getFullYear() }}
                </div>
                <div>
                  <strong>考試類型：</strong>
                  {{ getTypeName(form.type) }}
                </div>
                <div><strong>考試名稱：</strong> {{ form.filename }}</div>
                <div>
                  <strong>是否附解答：</strong>
                  {{ form.hasAnswers ? "是" : "否" }}
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

    <PdfPreviewModal
      :visible="showUploadPreview"
      @update:visible="showUploadPreview = $event"
      :previewUrl="uploadPreviewUrl"
      :title="form.file ? form.file.name : ''"
      :loading="uploadPreviewLoading"
      :error="uploadPreviewError"
      :showDownload="false"
      @hide="closeUploadPreview"
      @error="handleUploadPreviewError"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from "vue";
import { useToast } from "primevue/usetoast";
import { courseService, archiveService } from "../api";
import PdfPreviewModal from "./PdfPreviewModal.vue";
import { PDFDocument } from "pdf-lib";

const props = defineProps({
  modelValue: {
    type: Boolean,
    required: true,
  },
  coursesList: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["update:modelValue", "upload-success"]);

const toast = useToast();

const form = ref({
  category: null,
  subject: null,
  subjectId: null,
  professor: null,
  filename: "",
  type: null,
  hasAnswers: false,
  academicYear: null,
  file: null,
});

const uploadStep = ref("1");
const uploading = ref(false);
const fileUpload = ref(null);
const uploadFormProfessors = ref([]);
const isFilenameValid = ref(false);

const showUploadPreview = ref(false);
const uploadPreviewUrl = ref("");
const uploadPreviewLoading = ref(false);
const uploadPreviewError = ref(false);

const availableSubjects = ref([]);
const availableProfessors = ref([]);

const canGoToStep2 = computed(() => {
  return form.value.category && form.value.subject && form.value.professor;
});

const canGoToStep3 = computed(() => {
  return (
    form.value.academicYear &&
    form.value.type &&
    form.value.filename &&
    isFilenameValid.value
  );
});

const canUpload = computed(() => {
  return (
    form.value.file &&
    form.value.category &&
    form.value.subject &&
    form.value.professor &&
    form.value.academicYear &&
    form.value.type &&
    form.value.filename
  );
});

function validateFilename() {
  const regex = /^[a-z]+[0-9]*$/;
  isFilenameValid.value = regex.test(form.value.filename);
}

function getCategoryName(code) {
  const categories = {
    freshman: "大一課程",
    sophomore: "大二課程",
    junior: "大三課程",
    senior: "大四課程",
    graduate: "研究所課程",
    interdisciplinary: "跨領域課程",
    general: "通識課程",
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

function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}

async function fetchProfessorsForSubject(subjectId) {
  if (!subjectId) return;

  try {
    const response = await courseService.getCourseArchives(subjectId);
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

const handleUpload = async () => {
  try {
    uploading.value = true;

    const fileArrayBuffer = await form.value.file.arrayBuffer();
    const pdfDoc = await PDFDocument.load(fileArrayBuffer);

    pdfDoc.setTitle("");
    pdfDoc.setAuthor("");
    pdfDoc.setSubject("");
    pdfDoc.setKeywords([]);
    pdfDoc.setProducer("");
    pdfDoc.setCreator("");
    pdfDoc.setCreationDate(new Date());
    pdfDoc.setModificationDate(new Date());
    const pdfBytes = await pdfDoc.save();
    const cleanFile = new Blob([pdfBytes], { type: "application/pdf" });
    const cleanFileWithName = new File([cleanFile], form.value.file.name, {
      type: "application/pdf",
    });

    const formData = new FormData();
    formData.append("file", cleanFileWithName);
    formData.append("subject", form.value.subject);
    formData.append("category", form.value.category);
    formData.append("professor", form.value.professor);
    formData.append("archive_type", form.value.type);
    formData.append("has_answers", form.value.hasAnswers);
    formData.append("filename", form.value.filename);
    const year = new Date(form.value.academicYear).getFullYear();
    formData.append("academic_year", year);

    await archiveService.uploadArchive(formData);

    emit("update:modelValue", false);
    emit("upload-success");

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
      detail: "發生錯誤，請稍後再試",
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
  form.value.file = null;

  nextTick(() => {
    form.value.file = newFile;
  });
};

function clearSelectedFile(removeFileCallback) {
  if (removeFileCallback) removeFileCallback(0);
  form.value.file = null;
  if (fileUpload.value) {
    fileUpload.value.clear();
  }
}

function previewUploadFile() {
  if (!form.value.file) return;

  uploadPreviewLoading.value = true;
  uploadPreviewError.value = false;

  try {
    const fileUrl = URL.createObjectURL(
      new Blob([form.value.file], { type: "application/pdf" })
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

const searchSubject = (event) => {
  const query = event?.query?.toLowerCase() || "";
  const subjects = props.coursesList[form.value.category] || [];
  const filteredSubjects = subjects
    .map((course) => ({
      name: course.name,
      code: course.id,
    }))
    .filter((subject) => subject.name.toLowerCase().includes(query))
    .sort((a, b) => a.name.localeCompare(b.name));

  availableSubjects.value = filteredSubjects;
};

const searchProfessor = (event) => {
  const query = event?.query?.toLowerCase() || "";
  const filteredProfessors = uploadFormProfessors.value
    .filter((professor) => professor.name.toLowerCase().includes(query))
    .sort((a, b) => a.name.localeCompare(b.name));

  availableProfessors.value = filteredProfessors;
};

const onSubjectSelect = (event) => {
  form.value.subject = event.value.name;
  form.value.subjectId = event.value.code;
};

const onProfessorSelect = (event) => {
  if (event.value && typeof event.value === "object") {
    form.value.professor = event.value.name;
  }
};

watch(
  () => form.value.category,
  () => {
    form.value.subject = null;
    form.value.subjectId = null;
    form.value.professor = null;
  }
);

watch(
  () => form.value.subject,
  (newSubject) => {
    form.value.professor = null;
    if (newSubject) {
      fetchProfessorsForSubject(form.value.subjectId);
    } else {
      uploadFormProfessors.value = [];
    }
  }
);

watch(
  () => props.modelValue,
  (newValue, oldValue) => {
    if (oldValue === true && newValue === false) {
      resetForm();
    }
  }
);

function resetForm() {
  form.value = {
    category: null,
    subject: null,
    subjectId: null,
    professor: null,
    filename: "",
    type: null,
    hasAnswers: false,
    academicYear: null,
    file: null,
  };
  uploadStep.value = "1";
  isFilenameValid.value = false;
  availableSubjects.value = [];
  availableProfessors.value = [];
  uploadFormProfessors.value = [];

  if (fileUpload.value) {
    fileUpload.value.clear();
  }

  closeUploadPreview();
}
</script>

<style scoped>
.flex-wrap {
  flex-wrap: wrap;
}

.ellipsis {
  display: inline-block;
  max-width: 100%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  vertical-align: middle;
}
</style>
