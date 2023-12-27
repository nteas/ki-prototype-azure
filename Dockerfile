# build frontend
FROM node:18-alpine as frontend
# Define an ARG variable
ARG segment=segment

# Use the ARG variable to set an ENV variable
ENV VITE_SEGMENT_WRITE_KEY=$segment

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

COPY app/backend/requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt

COPY app/backend .
COPY --from=frontend app/backend/static /app/static

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--workers", "4"]