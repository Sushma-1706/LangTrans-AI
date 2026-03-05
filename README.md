# 🌍 LangTrans-AI

LangTrans-AI is a full-stack AI-powered multilingual audio-to-text platform that converts speech into accurate, structured text using high-performance inference powered by the Groq API.

It enables fast, scalable, and intelligent transcription across multiple languages through a modern web interface.

---

## 🚀 Features

- 🎙️ Multilingual audio transcription  
- 🌐 Optional translation to English  
- ⚡ High-speed AI inference using Groq API  
- 📝 Clean and structured text output  
- 🔁 Full-stack architecture (React + FastAPI)  
- 🎨 Modern and responsive UI  

---

## 🛠️ Tech Stack

### Frontend
- React
- Vite
- Tailwind CSS

### Backend
- Python
- FastAPI
- FFmpeg (local binary inside backend folder)

### AI Integration
- Groq API (LLM inference)

---

## 🔐 Environment Variables

Create a `.env` file inside the `backend` folder:

```env
GROQ_API_KEY=your_api_key_here
PORT=8000
```

⚠️ Never commit your `.env` file to GitHub.

---

## 📦 Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Sushma-1706/LangTrans-AI.git
cd LangTrans-AI
```

---

### 2️⃣ Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend runs at:
```
http://127.0.0.1:8000
```

---

### 3️⃣ Frontend Setup

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:
```
http://localhost:5173
```

---

## ⚙️ External Requirement

This project requires FFmpeg binaries to be present inside the `backend` folder:

- `backend/ffmpeg.exe`
- `backend/ffprobe.exe`

These files are not included in the repository and must be added manually.

---

## 📜 License

This project is licensed under the **MIT License**.

Note: The Groq API is a third-party service and subject to its own terms and licensing.

---

## 👩‍💻 Author

**Sushma Damacharla**  
AI & Frontend Developer
