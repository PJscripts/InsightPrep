import api from "./api";

export async function uploadResume(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post("/resumes/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
}
