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

docker build -t ai-prototype --build-arg segment=$VITE_SEGMENT_WRITE_KEY .

docker tag ai-prototype:latest tazdkntecr.azurecr.io/ai-prototype
