#!/bin/bash


echo 'Creating python virtual environment "venv"'
python3 -m venv venv

echo 'Activate python virtual environment "venv"'
source ./venv/bin/activate

echo ""
echo "Restoring backend python packages"
echo ""

./venv/bin/python -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to restore backend python packages"
    exit $?
fi

echo ""
echo "Restoring frontend npm packages"
echo ""

cd frontend
npm install
if [ $? -ne 0 ]; then
    echo "Failed to restore frontend npm packages"
    exit $?
fi

if [ ! -d "../app/static" ]; then
	echo "Building frontend for the first time"
	npm run build
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

cd ../app

port=50505
host=localhost
python3 -m uvicorn main:app --port "$port" --host "$host" --workers 4 --reload
if [ $? -ne 0 ]; then
	kill -9 $(lsof -i:3000 | grep node | awk '{print $2}')
    echo "Failed to start backend"
    exit $?
fi
