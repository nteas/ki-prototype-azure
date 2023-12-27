#!/bin/sh

echo ""
echo "Loading azd .env file from current environment"
echo ""

while IFS='=' read -r key value; do
    value=$(echo "$value" | sed 's/^"//' | sed 's/"$//')
    export "$key=$value"
done <<EOF
$(azd env get-values)
EOF

if [ $? -ne 0 ]; then
    echo "Failed to load environment variables from azd environment"
    exit $?
fi

cd app/backend
echo 'Creating python virtual environment "backend_env"'
python3 -m venv backend_env

echo ""
echo "Restoring backend python packages"
echo ""

./backend_env/bin/python -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to restore backend python packages"
    exit $?
fi

echo ""
echo "Restoring frontend npm packages"
echo ""

cd ../frontend
npm install
if [ $? -ne 0 ]; then
    echo "Failed to restore frontend npm packages"
    exit $?
fi

echo ""
echo "Building frontend"
echo ""

npm run dev &
if [ $? -ne 0 ]; then
    echo "Failed to build frontend"
    exit $?
fi

echo ""
echo "Starting backend"
echo ""

cd ../backend

port=50505
host=localhost
./backend_env/bin/python3 -m uvicorn main:app --port "$port" --host "$host" --workers 4 --reload
if [ $? -ne 0 ]; then
	kill -9 $(lsof -i:3000 | grep node | awk '{print $2}')
    echo "Failed to start backend"
    exit $?
fi
