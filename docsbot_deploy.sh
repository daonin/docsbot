#!/bin/bash

# Configuration
REPO_URL="https://github.com/daonin/docsbot.git"
REPO_DIR="docsbot"
IMAGE_NAME="docsbot"
CONTAINER_NAME="docsbot"
PRODCONFIG_PATH="/root/code/docsbot_prodconfig.yaml"

if [ ! -d "$REPO_DIR" ]; then
    echo "🔄 Cloning fresh repository..."
    git clone "$REPO_URL" "$REPO_DIR"
    cp "$PRODCONFIG_PATH" "$REPO_DIR/config.yaml"
    NEED_UPDATE=1
else
    echo "🔄 Checking for updates in master branch..."
    cd "$REPO_DIR"
    git fetch origin
    LOCAL_HASH=$(git rev-parse main)
    REMOTE_HASH=$(git rev-parse origin/main)
    if [ "$LOCAL_HASH" = "$REMOTE_HASH" ]; then
        echo "✅ No updates in master. Exiting."
        exit 0
    else
        echo "⬆️ Updates found. Pulling latest changes..."
        git reset --hard origin/main
        cp "$PRODCONFIG_PATH" ./config.yaml
        NEED_UPDATE=1
    fi
    cd ..
fi

if [ "$NEED_UPDATE" = "1" ]; then
    echo "🏗️ Building new image and starting container..."
    cd "$REPO_DIR"
    docker compose up -d --build
fi