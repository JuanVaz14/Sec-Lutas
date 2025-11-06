@echo off
echo ==================================================
echo 🚀 INICIANDO SISTEMA SEC-LUTAS
echo ==================================================
echo.

:: Ativa o ambiente virtual
call venv\Scripts\activate

:: Abre o servidor Flask em uma nova janela
start cmd /k "python app.py"

:: Aguarda 5 segundos pra garantir que o Flask inicialize
timeout /t 5 /nobreak >nul

:: Abre o Cloudflare Tunnel na mesma janela
echo 🌐 Iniciando Cloudflare Tunnel...
cloudflared-windows-amd64.exe tunnel --url http://localhost:5000

pause
