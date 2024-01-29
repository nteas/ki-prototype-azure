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

echo ""
echo "Starting backend"
echo ""

cd app/backend

./backend_env/bin/python3 main.py
if [ $? -ne 0 ]; then
	kill -9 $(lsof -i:3000 | grep node | awk '{print $2}')
    echo "Failed to start backend"
    exit $?
fi