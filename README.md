# 🤖 AI-Powered Document Scanner & OCR Web App

A Flask-based web application that uses advanced computer vision and machine learning to scan documents, extract text, and enhance images. This app allows users to upload document images, automatically detect their boundaries, perform perspective correction, and extract text using either **Tesseract OCR** or the powerful **Qwen2-VL-2B** model.

## ✨ Features

- **Document Boundary Detection**: Automatically identifies the corners of a document in an image.
- **Perspective Correction**: Straightens and crops the document to a flat, readable view.
- **Advanced OCR**:
  - **Tesseract OCR**: A robust open-source engine for fast text extraction.
  - **Qwen2-VL-2B**: A state-of-the-art multimodal model for superior accuracy, especially with complex layouts.
- **Intuitive Web Interface**: A user-friendly web UI for seamless interaction.
- **Image Preprocessing**: Includes automatic image enhancement for better OCR results.

## 🚀 Getting Started

### 📦 Prerequisites

- **Python 3.7+**
- **Tesseract OCR** installed on your system.
- A **CUDA-compatible GPU** (recommended for the Qwen2 model).

### 🛠️ Installation

1.  **Clone the Repository**:

    ```bash
    git clone https://github.com/Surfing-Cipher/Intelligent-Business-Card-Scanner.git
    cd Intelligent-Business-Card-Scanner
    ```

2.  **Set up a Virtual Environment**:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Dependencies**:

    ```bash
    pip install -r requirements_app.txt
    ```

4.  **Install Tesseract OCR**:

    - **Windows**: [Download installer](https://github.com/UB-Mannheim/tesseract/wiki)
    - **Linux**: `sudo apt-get install tesseract-ocr`
    - **macOS**: `brew install tesseract`

5.  **Download the Qwen2-VL-2B Model**:
    The model files should be placed in a directory named `Qwen2-VL-2B-OCR-fp16` within the project root.

---

## 🏃 Running the Application

1.  **Start the Flask server**:

    ```bash
    python main.py
    ```

2.  **Access the App**:
    Open your web browser and navigate to `http://localhost:5000`.

---

## 📝 Usage

1.  **Upload** an image of a document via the web interface.
2.  The app will automatically **detect boundaries**; you can adjust them if needed.
3.  Choose your desired **OCR model** (Tesseract or Qwen2).
4.  Click **"Extract Text"** to perform the processing and view the results.

---

## 📄 Project Structure

```
.
├── main.py               # Main Flask application entry point
├── predictions.py        # Logic for OCR prediction
├── templates/            # HTML templates
├── static/              # Static assets (CSS, JS)
├── requirements_app.txt   # Python dependencies
└── Qwen2-VL-2B-OCR-fp16/  # Directory for the Qwen2 model
```

---

## ⚠️ Notes & Troubleshooting

- For optimal results, ensure the document image is **well-lit** and **clear**.
- The Qwen2 model is computationally intensive and performs best on a **GPU with ample VRAM**.
- If you encounter issues, ensure all dependencies are installed, Tesseract is in your system's `PATH`, and the Qwen2 model is in the correct directory.

---

## 📜 License & Acknowledgments

This project is licensed under [Your License].

Special thanks to:

- **Flask** for the web framework.
- **OpenCV** for image processing.
- **Tesseract OCR** for text recognition.
- **Qwen2-VL-2B** for providing advanced OCR capabilities.
