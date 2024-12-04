#!/bin/bash

# Create required directories
mkdir -p static
mkdir -p staticfiles
mkdir -p media
mkdir -p logs

# Create a basic CSS file
echo "/* Base styles */" > static/style.css

# Create a basic JavaScript file
echo "// Base JavaScript" > static/main.js

# Set permissions
chmod -R 777 static staticfiles media logs