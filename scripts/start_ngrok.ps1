# Requires ngrok installed and on PATH
# Usage: ./start_ngrok.ps1
$port = 5000
Write-Host "Starting ngrok for port $port..."
ngrok http $port
