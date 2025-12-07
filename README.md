# 🚴‍♂️ Bike Price Finder

A Flask-based web application that fetches real-time bike prices from online sources.  
Easily deployable using Docker, lightweight, fast, and beginner-friendly.

---

## ⭐ Features

- 🔍 Search bike prices by brand & model  
- 🌐 Real-time data extraction  
- 🐳 Docker-based deployment  
- ⚡ Lightweight Flask backend  
- 📱 Simple and user-friendly UI  

---

## 🐳 Run Application Using Docker

### 1️⃣ Build Docker Image
 Run this inside the project folder:

 ```bash
 docker build -t bike_price_app .
```
### 2️⃣ Run
```bash
docker run -d --name bike_price_app -p 5000:5000 bike_price_app
```
### 3️⃣ Open in Browser
```cpp
http://127.0.0.1:5000
```

### 📁 Project Structure

```text
bike-price-app/
│── app1.py
│── requirements.txt
│── Dockerfile
```

---





