# QDoxie Home Assistant Integration

Home Assistant Integration für Doxie Scanner mit automatischem Upload zu Paperless-ngx
oder Ablage in einem Consume-Ordner.

## Features
- Regelmäßiges Polling der Doxie API
- Download neuer Scans
- Upload zu Paperless-ngx ODER Consume-Directory
- Löschen der Scans auf der Doxie nach Erfolg
- Sensoren:
  - Verbindungsstatus
  - Letzter Scan
  - Geräteinformationen

## Installation
1. Repository nach `custom_components/qdoxie` kopieren
2. Home Assistant neu starten
3. Integration über UI hinzufügen

## Konfiguration
### Upload-Modus
- `consume_dir`: Datei wird in Ordner geschrieben
- `paperless_api`: Datei wird per REST API hochgeladen

### Optionen
- Intervall (Sekunden)
- Paperless URL & Token
- Consume Directory Pfad

## Services
- `qdoxie.sync_now` – manueller Import

## Troubleshooting
### Config flow could not be loaded
- Domain in `manifest.json` und `config_flow.py` müssen identisch sein
- Home Assistant neu starten
