# build frontend
FROM node:18-alpine as frontend
COPY app/frontend app/frontend
WORKDIR /app/frontend
RUN npm install
RUN npm run build

# build backend
FROM python:3.10
# Install browser inside the container
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google-chrome.list
RUN apt-get update && apt-get install -y google-chrome-stable

WORKDIR /app/backend
COPY app/backend .
RUN pip install -r requirements.txt
COPY --from=frontend app/backend/static /app/backend/static

CMD ["python3", "-m", "uvicorn", "main:app", "--port", "8000", "--host", "0.0.0.0"]