
# 🌱 AI CropCare – Smart Crop Disease Detection System

AI CropCare is an AI-powered agricultural web application designed to help farmers identify possible crop diseases through image analysis and access smart farming information.

## 🚀 Project Overview

AI CropCare combines machine learning, Python Flask, MySQL, and web technologies to provide a digital farming support platform.

Farmers can upload crop images, receive AI-generated disease predictions, view treatment information, check weather conditions, and interact with an AI farming assistant.

## ✨ Key Features

### 👨‍🌾 Farmer Module
- Farmer registration and login
- Personal dashboard
- Crop disease image upload
- Detection history
- Farming analytics

### 🤖 Artificial Intelligence
- CNN-based crop disease classification
- Image preprocessing
- Disease prediction and confidence score
- Smart disease recommendations
- AI farming chatbot

### 🌦️ Weather Module
- Location-based weather search
- Temperature and humidity information
- Rainfall information
- Weather-based farming suggestions

### 🛠️ Admin Module
- Admin dashboard
- Farmer management
- Crop management
- Disease information management
- Detection monitoring

## 🧰 Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web framework |
| MySQL | Database |
| TensorFlow / Keras | Deep learning |
| NumPy | Image data processing |
| Pillow | Image processing |
| HTML5 | Web structure |
| CSS3 | User interface |
| JavaScript | Frontend interactions |
| OpenAI API | Farming chatbot |
| Open-Meteo API | Weather information |
| Cloudinary | Image storage |
| Hugging Face Hub | AI model hosting |
| Render | Application deployment |
| Git & GitHub | Version control |

## 🧠 AI Model Workflow

1. Farmer uploads a crop image.
2. The application validates the image.
3. The image is resized to 224 × 224 pixels.
4. Pixel values are normalized.
5. The trained CNN model predicts a class.
6. The application displays the predicted class and confidence.
7. Disease information is retrieved from MySQL.

## 📁 Project Structure

```text
AICropCare/
├── app.py
├── config.py
├── database.sql
├── requirements.txt
├── backend/
├── frontend/
├── ai/
├── models/
└── certificates/
```

## ⚙️ Installation

### 1. Clone repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd AICropCare
```

### 2. Create virtual environment

```bash
python -m venv venv
```

### 3. Activate environment on Windows

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file using `.env.example` as a reference.

Configure:
- Flask secret key
- MySQL credentials
- OpenAI API key
- Hugging Face repository and token, if private
- Cloudinary credentials

### 6. Configure MySQL

Execute `database.sql` using MySQL Workbench or your MySQL client.

### 7. Run application

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## ☁️ Deployment

The application can be deployed using:
- GitHub for source code
- Render for Flask hosting
- Managed MySQL for database
- Hugging Face Hub for model files
- Cloudinary for uploaded images

Configure all credentials as deployment environment variables.

## 🔒 Security

- Password hashing
- CSRF protection
- Login rate limiting
- Secure session cookies
- Image upload validation
- Role-based admin access
- Environment-based secrets

## ⚠️ Disclaimer

AI CropCare provides experimental AI predictions and general farming information. Predictions may be incorrect. Farmers should confirm serious crop disease issues with qualified agricultural experts before applying treatments.

## 👨‍💻 Developer

**Goskula Mallesh**

Python Full Stack Developer | Fresher

Skills:
Python | Flask | MySQL | HTML | CSS | JavaScript | APIs | Machine Learning

Location: Karimnagar, Telangana, India

Portfolio:
https://goskulamallesh.pythonanywhere.com/

LinkedIn:
https://linkedin.com/in/mallesh-goskula-2939b5397
