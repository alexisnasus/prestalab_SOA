#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Monitor de Servicios SOA - PrestaLab
    
.DESCRIPTION
    Script que abre múltiples ventanas de PowerShell, cada una monitoreando
    un servicio diferente de la arquitectura SOA. Perfecto para demostrar
    la trazabilidad y el flujo de mensajes en tiempo real.
    
.NOTES
    Autor: Sistema de Trazabilidad SOA
    Fecha: Octubre 2025
    Version: 1.0.0
#>

# Configuracion
$ErrorActionPreference = "Stop"

# Banner de inicio
Clear-Host
Write-Host ""
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "    >> MONITOR DE SERVICIOS SOA - PRESTALAB <<" -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si Docker esta corriendo
Write-Host "[1/4] Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerInfo = docker version --format '{{.Server.Version}}' 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($dockerInfo)) {
        Write-Host "[X] Docker no esta corriendo. Por favor inicia Docker Desktop." -ForegroundColor Red
        exit 1
    }
    Write-Host "    [OK] Docker esta corriendo (version: $($dockerInfo.Trim()))" -ForegroundColor Green
} catch {
    Write-Host "[X] Error al verificar Docker. Asegurate de que Docker Desktop este iniciado." -ForegroundColor Red
    exit 1
}

# Verificar si estamos en el directorio correcto
Write-Host "[2/4] Verificando directorio..." -ForegroundColor Yellow
if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "[X] No se encuentra docker-compose.yml" -ForegroundColor Red
    Write-Host "   Por favor ejecuta este script desde la carpeta 'backend'" -ForegroundColor Red
    exit 1
}
Write-Host "    [OK] Directorio correcto" -ForegroundColor Green

# Levantar servicios en background
Write-Host "[3/4] Levantando servicios en background..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "[X] Error al levantar servicios" -ForegroundColor Red
    exit 1
}

# Esperar a que los servicios inicien
Write-Host "    Esperando a que los servicios inicien..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Verificar que los contenedores esten corriendo
$runningContainers = docker-compose ps --services --filter "status=running"
Write-Host "    [OK] Servicios levantados: $($runningContainers.Count)" -ForegroundColor Green

# Array de servicios a monitorear
$services = @(
    @{
        Name = "BUS ESB"
        Container = "soa_bus"
        Color = "Cyan"
        Icon = "[BUS]"
        Description = "Enterprise Service Bus - Enrutador central"
    },
    @{
        Name = "REGIST"
        Container = "soa_regist"
        Color = "Green"
        Icon = "[USR]"
        Description = "Gestion de Usuarios y Autenticacion"
    },
    @{
        Name = "PRART"
        Container = "soa_prart"
        Color = "Yellow"
        Icon = "[ART]"
        Description = "Prestamos y Articulos"
    },
    @{
        Name = "MULTA"
        Container = "soa_multa"
        Color = "Red"
        Icon = "[MLT]"
        Description = "Gestion de Multas"
    },
    @{
        Name = "LISTA"
        Container = "soa_lista"
        Color = "Magenta"
        Icon = "[LST]"
        Description = "Listas de Espera"
    },
    @{
        Name = "NOTIS"
        Container = "soa_notis"
        Color = "Blue"
        Icon = "[NOT]"
        Description = "Notificaciones"
    },
    @{
        Name = "GEREP"
        Container = "soa_gerep"
        Color = "DarkYellow"
        Icon = "[REP]"
        Description = "Gestion de Reportes"
    },
    @{
        Name = "SUGIT"
        Container = "soa_sugit"
        Color = "DarkCyan"
        Icon = "[SUG]"
        Description = "Sugerencias"
    }
)

# Abrir una ventana de PowerShell para cada servicio
Write-Host "[4/4] Abriendo monitores..." -ForegroundColor Yellow

$windowCount = 0
$processIds = @()  # Array para guardar los IDs de los procesos creados

foreach ($service in $services) {
    $title = "SOA - $($service.Name)"
    
    # Comando que se ejecutara en cada ventana
    $command = @"
`$Host.UI.RawUI.WindowTitle = '$title'
Write-Host ''
Write-Host '===================================================================' -ForegroundColor $($service.Color)
Write-Host '    $($service.Icon) SERVICIO: $($service.Name)' -ForegroundColor $($service.Color)
Write-Host '    Container: $($service.Container)' -ForegroundColor $($service.Color)
Write-Host '    $($service.Description)' -ForegroundColor $($service.Color)
Write-Host '===================================================================' -ForegroundColor $($service.Color)
Write-Host ''
Write-Host 'Conectando al stream de logs...' -ForegroundColor Gray
Write-Host ''

# Seguir logs del contenedor
docker logs -f $($service.Container) 2>&1 | ForEach-Object {
    `$line = `$_
    
    # Colorear lineas especiales
    if (`$line -match 'ERROR|Error|error|FAILED|Failed') {
        Write-Host `$line -ForegroundColor Red
    }
    elseif (`$line -match 'WARNING|Warning|warning') {
        Write-Host `$line -ForegroundColor Yellow
    }
    elseif (`$line -match 'SUCCESS|Success|success') {
        Write-Host `$line -ForegroundColor Green
    }
    elseif (`$line -match 'REQUEST|RESPONSE') {
        Write-Host `$line -ForegroundColor Cyan
    }
    elseif (`$line -match 'DB QUERY|SQL') {
        Write-Host `$line -ForegroundColor Magenta
    }
    else {
        Write-Host `$line
    }
}
"@
    
    # Crear archivo temporal con el comando
    $tempScript = [System.IO.Path]::GetTempFileName() + ".ps1"
    $command | Out-File -FilePath $tempScript -Encoding UTF8
    
    # Abrir nueva ventana de PowerShell ejecutando el script temporal
    $process = Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", $tempScript -PassThru
    
    # Guardar el ID del proceso
    $processIds += $process.Id
    
    $windowCount++
    Write-Host "    [OK] Monitor $windowCount/$($services.Count): $($service.Icon) $($service.Name) (PID: $($process.Id))" -ForegroundColor Green
    
    # Pequeña pausa para no saturar
    Start-Sleep -Milliseconds 800
}

Write-Host ""
Write-Host "===================================================================" -ForegroundColor Green
Write-Host "    [OK] TODOS LOS MONITORES INICIADOS ($windowCount ventanas)" -ForegroundColor Green
Write-Host "===================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Informacion util:" -ForegroundColor Cyan
Write-Host "   - Bus ESB:      http://localhost:8000" -ForegroundColor White
Write-Host "   - PHPMyAdmin:   http://localhost:8080" -ForegroundColor White
Write-Host "   - Servicios:    puertos 8001-8007" -ForegroundColor White
Write-Host ""
Write-Host "Comandos utiles:" -ForegroundColor Cyan
Write-Host "   - Ver servicios:     docker-compose ps" -ForegroundColor White
Write-Host "   - Ver estadisticas:  curl http://localhost:8000/stats" -ForegroundColor White
Write-Host "   - Ver servicios reg: curl http://localhost:8000/discover" -ForegroundColor White
Write-Host ""
Write-Host "Ejemplo de peticion de prueba:" -ForegroundColor Cyan
Write-Host '   $json = @"' -ForegroundColor Gray
Write-Host '   {' -ForegroundColor Gray
Write-Host '     "target_service": "regist",' -ForegroundColor Gray
Write-Host '     "method": "GET",' -ForegroundColor Gray
Write-Host '     "endpoint": "/usuarios/140987654"' -ForegroundColor Gray
Write-Host '   }' -ForegroundColor Gray
Write-Host '   "@' -ForegroundColor Gray
Write-Host '   Invoke-RestMethod -Uri "http://localhost:8000/route" -Method Post -ContentType "application/json" -Body $json' -ForegroundColor Gray
Write-Host ""
Write-Host "===================================================================" -ForegroundColor Yellow
Write-Host "    [!] PRESIONA CUALQUIER TECLA PARA DETENER TODOS LOS SERVICIOS" -ForegroundColor Yellow
Write-Host "===================================================================" -ForegroundColor Yellow
Write-Host ""

# Esperar input del usuario
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Cerrar todas las ventanas de monitoreo
Write-Host ""
Write-Host "Cerrando ventanas de monitoreo..." -ForegroundColor Yellow
foreach ($processId in $processIds) {
    try {
        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
        Write-Host "  [OK] Ventana cerrada (PID: $processId)" -ForegroundColor Green
    } catch {
        # Ignorar errores si el proceso ya no existe
    }
}

# Detener servicios
Write-Host ""
Write-Host "Deteniendo servicios..." -ForegroundColor Yellow
docker-compose down

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Servicios detenidos correctamente." -ForegroundColor Green
} else {
    Write-Host "[!] Hubo un problema al detener los servicios." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Hasta pronto!" -ForegroundColor Cyan
Write-Host ""

# Limpiar archivos temporales
Get-ChildItem $env:TEMP -Filter "tmp*.ps1" | Remove-Item -ErrorAction SilentlyContinue

# Pausa final
Start-Sleep -Seconds 2
