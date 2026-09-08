const inputf = document.getElementById("pdfFile");
const button = document.getElementById("uploadButton");
const result = document.getElementById("result");
const inputt = document.getElementById("query-input")

button.addEventListener("click", uploadPDF);


async function uploadPDF() {

    const file = inputf.files[0];
    const text = inputt.value;

    if (!file) {
        alert("Сначала выберите PDF");
        return;
    }

    const formData = new FormData();

    formData.append("file", file);
    formData.append("question", text);


    const response = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData
    });

const data = await response.json();

// Сохраняем весь объект в хранилище сессии
sessionStorage.setItem('analyticsData', JSON.stringify(data));

    window.location.href = "result.html";
}
