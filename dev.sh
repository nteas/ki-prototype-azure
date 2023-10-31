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
npm_pid=$!  # Save the PID of the npm process

trap "kill $npm_pid" EXIT  # Add a trap to kill the npm process when the script exits

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
./backend_env/bin/python -m quart --app main:app run --port "$port" --host "$host" --reload &
python_pid=$!

if [ $? -ne 0 ]; then
    echo "Failed to start backend"
    kill $python_pid  # Use the python_pid variable
	kill $npm_pid  # Use the npm_pid variable
    exit $?
fi

# Wait for the Python process to finish