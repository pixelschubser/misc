# WSL2 + VS Code Dev Containers auf der Citrix/VMware-VDI

> Stand: 2026-10-23

## Inhalt

- [Kurzanleitung](#kurzanleitung)
- [Überblick](#überblick)
- [Schritt 0: Voraussetzungen prüfen](#schritt-0-voraussetzungen-prüfen)
- [Schritt 1: Windows-Features aktivieren (Admin-Konto)](#schritt-1-windows-features-aktivieren-admin-konto)
- [Schritt 2: WSL-Paket installieren (Admin-Konto)](#schritt-2-wsl-paket-installieren-admin-konto)
- [Schritt 3: Ubuntu nach C:\MYSOFT\WSL installieren (normales Konto)](#schritt-3-ubuntu-nach-cmysoftwsl-installieren-normales-konto)
- [Schritt 4: WSL konfigurieren](#schritt-4-wsl-konfigurieren-wslconfig-und-wslconf)
- [Schritt 5: Firmen-Proxy und Zertifikate in WSL](#schritt-5-firmen-proxy-und-zertifikate-in-wsl)
- [Schritt 6: Docker Engine in Ubuntu installieren](#schritt-6-docker-engine-in-ubuntu-installieren)
- [Schritt 7: VS Code installieren und Dev Containers einrichten](#schritt-7-vs-code-installieren-und-dev-containers-einrichten)
- [Schritt 8: Funktionstest mit einem Beispiel-Dev-Container](#schritt-8-funktionstest-mit-einem-beispiel-dev-container)
- [Fehlerbehebung](#fehlerbehebung)
- [Was du ggf. bei der IT anfragen musst](#was-du-ggf-bei-der-it-anfragen-musst)

---

## Kurzanleitung

**[N]** = normales Konto · **[A]** = Admin-Konto · Details zu jedem Schritt in den Abschnitten darunter.

### A. Prüfen (5 Min.)

1. **[N]** Windows-Version: `winver` → Windows 11 oder Windows 10 22H2.
2. **[N]** Virtualisierung: `systeminfo` → „Virtualisierung in Firmware aktiviert: Ja“ oder „Hypervisor erkannt“. Sonst IT-Ticket (siehe Ende).
3. **[N]** Ordner anlegen: `mkdir C:\MYSOFT\WSL\Ubuntu`. Klappt das nicht → Schritt 5 dieser Kurzanleitung.

### B. Windows vorbereiten (Admin-Konto)

4. **[A]** PowerShell öffnen: Startmenü → PowerShell → Rechtsklick → *Als Administrator ausführen* → Admin-Zugangsdaten.
5. **[A]** Features einschalten (und ggf. Ordnerrechte):

   ```powershell
   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
   icacls C:\MYSOFT\WSL /grant "DOMÄNE\normales-konto:(OI)(CI)M"
   ```

6. **[N]** WSL-MSI von [github.com/microsoft/WSL/releases](https://github.com/microsoft/WSL/releases) (`wsl.<version>.x64.msi`) nach `C:\MYSOFT\TEMP` herunterladen.
7. **[A]** Installieren: `msiexec /i "C:\MYSOFT\TEMP\wsl.<version>.x64.msi"`
8. VDI **neu starten**.

### C. Ubuntu einrichten (ab hier nur normales Konto)

9. **[N]** PowerShell (ohne Admin):

   ```powershell
   wsl --version                 # muss 2.x zeigen
   wsl --set-default-version 2
   wsl --install -d Ubuntu-24.04 --web-download --location C:\MYSOFT\WSL\Ubuntu
   ```

   Benutzername und Passwort für Linux vergeben. Klappt der Download nicht → Variante B in Schritt 3 (Offline-Import).

10. **[N]** `notepad $env:USERPROFILE\.wslconfig`:

    ```ini
    [wsl2]
    memory=8GB
    processors=4
    networkingMode=mirrored
    dnsTunneling=true
    autoProxy=true
    ```

11. In Ubuntu `sudo nano /etc/wsl.conf`:

    ```ini
    [boot]
    systemd=true
    ```

12. In PowerShell `wsl --shutdown`, dann `wsl`.
13. Netz testen: `curl -sSI https://github.com | head -1`. Fehler → Proxy/Zertifikat nach Schritt 5.

### D. Docker in Ubuntu

14. Docker Engine installieren:

    ```bash
    sudo apt-get update && sudo apt-get install -y ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    echo "deb [signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list
    sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo usermod -aG docker $USER
    ```

15. In PowerShell `wsl --terminate Ubuntu`, Ubuntu neu öffnen, dann `docker run --rm hello-world`.

### E. VS Code

16. **[N]** VS Code „User Installer x64“ oder ZIP nach `C:\MYSOFT\VSCode` (Schritt 7.1).
17. Erweiterungen **WSL** und **Dev Containers** installieren.
18. User Settings (JSON) ergänzen: `"dev.containers.executeInWSL": true`
19. In Ubuntu: `mkdir -p ~/projects && cd ~/projects`, Repo klonen, `code .`
20. Strg+Shift+P → **Dev Containers: Reopen in Container**. Fertig.

---

## Überblick

Ziel: VS Code läuft unter Windows in der VDI. Quellcode, Docker Engine und Dev Container laufen in einer Ubuntu-Instanz unter WSL2 – ohne Docker Desktop. Das spart Lizenzkosten (Docker Desktop ist in Unternehmen ab 250 Mitarbeitern kostenpflichtig) und eine zusätzliche Fehlerquelle.

Die größte Hürde ist nicht die Installation, sondern die VDI: WSL2 ist selbst eine kleine VM. In einer VMware-VM braucht es daher **Nested Virtualization**. Ist sie nicht aktiv, scheitert alles Weitere. Prüfe deshalb zuerst Schritt 0, bevor du Zeit investierst.

**Welches Konto wofür** – das ist der häufigste Stolperstein:

| Aufgabe | Konto | Warum |
| --- | --- | --- |
| Windows-Features aktivieren, WSL-Paket (MSI) installieren | Admin-Konto | Systemweite Änderung, braucht Adminrechte |
| Schreibrechte auf `C:\MYSOFT\WSL` für dein normales Konto setzen (falls nötig) | Admin-Konto | NTFS-Rechte |
| Ubuntu-Distribution importieren, `.wslconfig`, alles innerhalb von Ubuntu | Normales Konto | Distributionen sind **pro Windows-Benutzer** registriert |
| VS Code (User Installer) und Extensions | Normales Konto | Installiert ins Benutzerprofil, keine Adminrechte nötig |

Wichtig: Startest du `wsl --install` in einer Admin-Konsole, landet die Ubuntu-Distribution im Profil des Admin-Kontos. Dein normales Konto sieht sie dann nicht. Deshalb trennt diese Anleitung bewusst „WSL installieren“ (Admin) und „Distribution anlegen“ (normales Konto).

So öffnest du eine Admin-Konsole aus deiner normalen Sitzung: Startmenü → „PowerShell“ suchen → Rechtsklick → *Als anderer Benutzer ausführen* bzw. *Als Administrator ausführen* und die Daten des Admin-Kontos eingeben. Alternativ: `runas /user:DOMÄNE\admin-konto powershell`.

## Schritt 0: Voraussetzungen prüfen

Diese fünf Prüfungen dauern etwa zehn Minuten und entscheiden, ob WSL2 in deiner VDI überhaupt funktionieren kann. Alle laufen im **normalen Konto** in einer PowerShell.

**0.1 Windows-Version.** `winver` ausführen. Nötig ist Windows 11 oder Windows 10 ab 22H2 (Build 19045). Ältere Builds unterstützen das aktuelle WSL-Paket nicht zuverlässig.

**0.2 Nested Virtualization.** Das ist der kritische Punkt.

```powershell
systeminfo | Select-String "Hyper-V", "Hypervisor"
Get-CimInstance Win32_Processor | Select-Object Name, VirtualizationFirmwareEnabled
```

So liest du das Ergebnis:

- „Es wurde ein Hypervisor erkannt“ / „A hypervisor has been detected“: Ein Hypervisor läuft bereits (z. B. wegen VBS/Credential Guard). Gutes Zeichen, aber noch kein Beweis.
- Vier Zeilen „Hyper-V-Anforderungen“ mit „Ja“ und „Virtualisierung in Firmware aktiviert: Ja“: Die VM sieht die Virtualisierungsfunktionen der CPU. Sehr gut.
- „Virtualisierung in Firmware aktiviert: Nein“: VMware reicht VT-x/AMD-V nicht an die VM durch. WSL2 wird mit Fehler `0x80370102` scheitern. Dann brauchst du die IT (siehe letzter Abschnitt) – auf VMware-Seite muss „Expose hardware assisted virtualization to the guest OS“ (`vhv.enable = TRUE`) für die VM bzw. das Golden Image gesetzt werden.

Den endgültigen Beweis liefert erst Schritt 3: Startet die Distribution mit `--version 2`, funktioniert es.

**0.3 Persistente oder nicht-persistente VDI?** Citrix-VDIs werden oft aus einem Master-Image erzeugt und bei der Abmeldung zurückgesetzt (MCS/PVS, „non-persistent“). Dann wären Ubuntu, Docker-Images und dein Code nach jedem Neustart weg. Prüfe:

1. Lege eine Testdatei `C:\MYSOFT\test.txt` an.
2. Melde dich ab, starte die VDI neu, melde dich wieder an.
3. Ist die Datei noch da, ist `C:\` persistent. Prüfe dasselbe mit einer Datei in `%LOCALAPPDATA%`.

Ist nichts persistent, frag die IT nach einem persistenten Laufwerk oder einer dedizierten (persistenten) VDI. Ohne Persistenz lohnt sich der Aufwand nicht.

**0.4 Schreibrechte und Platz auf `C:\MYSOFT`.** Die WSL-Festplatte (`ext4.vhdx`) soll nach `C:\MYSOFT\WSL`, weil dieses Verzeichnis vom Virenscanner ausgenommen ist. Das macht Dateizugriffe und Docker-Builds spürbar schneller. Prüfe im **normalen** Konto:

```powershell
New-Item -ItemType Directory C:\MYSOFT\WSL\Ubuntu -Force
Get-PSDrive C
```

Schlägt das Anlegen fehl, gib deinem normalen Konto mit dem Admin-Konto Rechte darauf (Schritt 1). Plane mindestens 30–50 GB freien Platz ein; Docker-Images wachsen schnell.

**0.5 Organisationsrichtlinie.** Manche Firmen sperren WSL per Gruppenrichtlinie/Intune. Erkennbar an Meldungen wie „WSL is disabled by your organization“ – dann hilft nur die IT.

## Schritt 1: Windows-Features aktivieren (Admin-Konto)

WSL2 braucht zwei Windows-Komponenten: das „Windows-Subsystem für Linux“ und die „VM-Plattform“. Beides schaltest du einmalig mit dem Admin-Konto ein.

Öffne eine PowerShell **als Admin-Konto** (siehe Überblick) und führe aus:

```powershell
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
```

Erklärung: `Microsoft-Windows-Subsystem-Linux` ist die WSL-Grundlage, `VirtualMachinePlatform` stellt die leichtgewichtige Hyper-V-Schicht bereit, auf der WSL2 seine Linux-VM betreibt. `/norestart` verhindert einen sofortigen Neustart, damit du beide Befehle nacheinander ausführen kannst.

Prüfen:

```powershell
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux, VirtualMachinePlatform | Select-Object FeatureName, State
```

Beide müssen `Enabled` zeigen (bzw. `EnablePending` vor dem Neustart).

**Falls nötig: Rechte auf `C:\MYSOFT\WSL`** für dein normales Konto vergeben (nur wenn Schritt 0.4 gescheitert ist):

```powershell
New-Item -ItemType Directory C:\MYSOFT\WSL -Force
icacls C:\MYSOFT\WSL /grant "DOMÄNE\dein-normales-konto:(OI)(CI)M"
```

`(OI)(CI)M` bedeutet: Ändern-Recht, vererbt auf alle Unterordner und Dateien.

**Danach die VDI neu starten** (Startmenü → Neu starten, nicht nur abmelden). Bei nicht-persistenten Maschinen gehen die Features dabei verloren – siehe Schritt 0.3.

Wenn `dism` mit „Zugriff verweigert“ oder Fehler `0x800f0922` abbricht, ist dein Admin-Konto für Feature-Änderungen gesperrt. Dann muss die IT die Features im Image aktivieren.

## Schritt 2: WSL-Paket installieren (Admin-Konto)

Die in Windows eingebaute WSL-Version ist veraltet. Das aktuelle WSL kommt als eigenes Paket, normalerweise über den Microsoft Store. In Firmen-VDIs ist der Store meist gesperrt, deshalb nutzt du das offizielle MSI-Paket von GitHub.

1. Lade im Browser von [github.com/microsoft/WSL/releases](https://github.com/microsoft/WSL/releases) das neueste stabile Release herunter (nicht „Pre-release“). Die Datei heißt `wsl.<version>.x64.msi`.
2. Speichere sie nach `C:\MYSOFT\TEMP`.
3. Installiere sie in einer PowerShell **als Admin-Konto**:

   ```powershell
   msiexec /i "C:\MYSOFT\TEMP\wsl.<version>.x64.msi"
   ```

   Das MSI installiert WSL systemweit nach `C:\Program Files\WSL`. Damit steht es allen Benutzern der VDI zur Verfügung, also auch deinem normalen Konto.

4. Prüfe als **normales Konto** in einer neuen PowerShell:

   ```powershell
   wsl --version
   wsl --set-default-version 2
   ```

`wsl --version` muss eine WSL-Version 2.x anzeigen. Kommt stattdessen eine Hilfeseite oder „unbekannte Option“, läuft noch das alte eingebaute WSL – dann hat das MSI nicht gegriffen. `--set-default-version 2` gilt pro Benutzer und sorgt dafür, dass neue Distributionen als WSL2 (echte Linux-VM) und nicht als WSL1 angelegt werden.

Später aktualisierst du WSL, indem du ein neueres MSI genauso installierst. `wsl --update` funktioniert nur, wenn Store oder GitHub erreichbar sind; mit `wsl --update --web-download` kannst du es direkt über GitHub versuchen.

## Schritt 3: Ubuntu nach C:\MYSOFT\WSL installieren (normales Konto)

Ab hier arbeitest du nur noch mit deinem **normalen Konto**. Die Distribution landet als virtuelle Festplatte (`ext4.vhdx`) in `C:\MYSOFT\WSL\Ubuntu` – außerhalb des Virenscanners und nicht im (evtl. servergespeicherten) Citrix-Profil.

**Variante A – Online-Installation mit Zielordner** (aktuelle WSL-Versionen):

```powershell
wsl --install -d Ubuntu-24.04 --web-download --location C:\MYSOFT\WSL\Ubuntu
```

`--web-download` lädt direkt von GitHub/Ubuntu statt aus dem Store, `--location` legt die Festplatte in deinen Ordner. Ubuntu fragt beim ersten Start nach Benutzername und Passwort – das ist dein Linux-Konto, unabhängig vom Windows-Konto. Kennt dein WSL `--location` nicht oder ist der Download blockiert, nimm Variante B.

**Variante B – Offline-Import** (funktioniert immer, wenn du die Datei herunterladen kannst):

1. Lade das WSL-Image von Ubuntu herunter, z. B. von [cloud-images.ubuntu.com/wsl](https://cloud-images.ubuntu.com/wsl/) (Ordner für 24.04 „noble“, Datei mit `amd64` und Endung `.rootfs.tar.gz` bzw. `.wsl`) und speichere es nach `C:\MYSOFT\TEMP`.
2. Importieren:

   ```powershell
   wsl --import Ubuntu C:\MYSOFT\WSL\Ubuntu C:\MYSOFT\TEMP\<dateiname> --version 2
   wsl --set-default Ubuntu
   wsl -l -v
   ```

   In der Ausgabe von `wsl -l -v` muss bei Ubuntu **VERSION 2** stehen und der Status nach dem ersten Start `Running` sein. Kommt hier `0x80370102`, fehlt Nested Virtualization (Schritt 0.2).

3. Ein importiertes Image startet als `root`. Lege deinen Linux-Benutzer an:

   ```bash
   wsl -d Ubuntu
   # jetzt in Ubuntu als root:
   adduser ed
   usermod -aG sudo ed
   printf '[user]\ndefault=ed\n' >> /etc/wsl.conf
   exit
   ```

4. In PowerShell `wsl --terminate Ubuntu` und danach `wsl` – du solltest nun als `ed` angemeldet sein.

**Erstes Update** in Ubuntu (falls ein Proxy nötig ist, zuerst Schritt 5 erledigen):

```bash
sudo apt update && sudo apt upgrade -y
```

Tipp: Ein Backup der kompletten Umgebung machst du jederzeit mit `wsl --export Ubuntu C:\MYSOFT\TEMP\ubuntu-backup.tar` – praktisch, bevor du experimentierst oder falls die VDI neu aufgesetzt wird.

## Schritt 4: WSL konfigurieren (.wslconfig und wsl.conf)

Es gibt zwei Konfigurationsdateien: `.wslconfig` unter Windows steuert die WSL2-VM als Ganzes (RAM, CPU, Netzwerk), `/etc/wsl.conf` in Ubuntu steuert die einzelne Distribution (systemd, Standardbenutzer).

**4.1 `.wslconfig` – Ressourcen und Netzwerk** (normales Konto). Lege die Datei `C:\Users\<dein-konto>\.wslconfig` an (`notepad $env:USERPROFILE\.wslconfig`):

```ini
[wsl2]
# Etwa die Hälfte des VDI-RAMs; VDIs haben oft nur 16 GB
memory=8GB
processors=4
swap=4GB

# Netzwerk: Windows und WSL teilen sich Netzwerk, VPN und Proxy
# (nur Windows 11 22H2+; unter Windows 10 diese drei Zeilen weglassen)
networkingMode=mirrored
dnsTunneling=true
autoProxy=true

[experimental]
# gibt ungenutzten RAM an die VDI zurück
autoMemoryReclaim=gradual
# lässt die vhdx-Datei wieder schrumpfen
sparseVhd=true
```

Warum das wichtig ist: Ohne `memory`-Grenze darf WSL2 standardmäßig bis zur Hälfte des RAMs belegen und gibt ihn nur zögerlich zurück. In einer knapp ausgestatteten VDI wird Windows dann träge. Passe `memory` und `processors` an deine VDI an (`Get-CimInstance Win32_ComputerSystem` zeigt RAM, Task-Manager die Kerne).

`networkingMode=mirrored` ist in Firmennetzen meist die bessere Wahl: WSL bekommt dieselbe Netzwerksicht wie Windows, `localhost` funktioniert in beide Richtungen, und das klassische Problem „WSL-Subnetz 172.x kollidiert mit dem Firmennetz“ entfällt. `dnsTunneling` leitet DNS-Anfragen über Windows, `autoProxy` übernimmt die Proxy-Einstellung von Windows für WSL.

**4.2 `/etc/wsl.conf` – systemd einschalten** (in Ubuntu). Docker braucht einen Dienst-Manager; mit systemd startet Docker automatisch.

```bash
sudo nano /etc/wsl.conf
```

Inhalt:

```ini
[boot]
systemd=true

[user]
default=ed
```

**4.3 Neu starten**, damit beide Dateien wirken (PowerShell):

```powershell
wsl --shutdown
# ca. 8 Sekunden warten, dann
wsl
```

Prüfen in Ubuntu: `systemctl is-system-running` sollte `running` oder `degraded` liefern (degraded ist unter WSL normal). „System has not been booted with systemd“ heißt: `wsl.conf` wurde nicht gelesen.

## Schritt 5: Firmen-Proxy und Zertifikate in WSL

In Firmennetzen scheitern `apt`, `curl`, Docker-Pulls und der VS-Code-Server-Download fast immer an zwei Dingen: einem Proxy und einer TLS-Inspektion mit firmeneigenem Root-Zertifikat. Prüfe beides, bevor du Docker installierst.

**5.1 Test** in Ubuntu:

```bash
curl -sSI https://github.com | head -1
env | grep -i proxy
```

- `HTTP/2 200` → Netzwerk funktioniert, du kannst Schritt 5 überspringen.
- Timeout / „Could not resolve host“ → Proxy fehlt (5.2).
- „SSL certificate problem: self-signed certificate in certificate chain“ → TLS-Inspektion, Zertifikat fehlt (5.3).

**5.2 Proxy ermitteln und setzen.** Unter Windows (PowerShell):

```powershell
netsh winhttp show proxy
Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' | Select-Object ProxyServer, AutoConfigURL
```

Steht dort nur eine `AutoConfigURL` (PAC-Datei), öffne sie im Browser und suche den `PROXY host:port`-Eintrag. Dann in Ubuntu in `~/.bashrc` ergänzen (Werte anpassen):

```bash
export http_proxy="http://proxy.firma.example:8080"
export https_proxy="$http_proxy"
export no_proxy="localhost,127.0.0.1,::1,.firma.example"
export HTTP_PROXY="$http_proxy" HTTPS_PROXY="$https_proxy" NO_PROXY="$no_proxy"
```

`apt` liest diese Variablen bei `sudo` nicht zuverlässig, deshalb zusätzlich:

```bash
sudo tee /etc/apt/apt.conf.d/95proxy <<'EOF'
Acquire::http::Proxy "http://proxy.firma.example:8080";
Acquire::https::Proxy "http://proxy.firma.example:8080";
EOF
```

Verlangt der Proxy eine Anmeldung, frag die IT nach einem Weg ohne Klartext-Passwort (z. B. Ausnahme für Paketquellen); Passwörter in `.bashrc` sind keine gute Idee.

**5.3 Firmen-Root-Zertifikat importieren.** So findest du es: In Edge `https://github.com` öffnen → Schloss-Symbol → Zertifikat anzeigen → oberstes Zertifikat der Kette. Steht dort ein Firmenname statt einer öffentlichen CA, ist TLS-Inspektion aktiv. Exportiere dieses Zertifikat (Details → Exportieren, Format „Base-64-codiert X.509“) nach `C:\MYSOFT\TEMP\firma-root.cer`. Dann in Ubuntu:

```bash
sudo cp /mnt/c/MYSOFT/TEMP/firma-root.cer /usr/local/share/ca-certificates/firma-root.crt
sudo update-ca-certificates
curl -sSI https://github.com | head -1
```

Die Endung muss `.crt` sein, sonst ignoriert `update-ca-certificates` die Datei. Hast du stattdessen eine DER-Datei exportiert: `openssl x509 -inform der -in … -out …crt`.

Merke dir Proxy und Zertifikat – beide brauchst du in Schritt 6 (Docker-Daemon) und Schritt 8 (in den Containern) noch einmal.

## Schritt 6: Docker Engine in Ubuntu installieren

Du installierst Docker direkt in Ubuntu aus dem offiziellen Docker-Repository – genauso wie auf einem Linux-Server. Docker Desktop für Windows brauchst du nicht; VS Code spricht später direkt mit diesem Docker in WSL.

**6.1 Repository einrichten und installieren** (in Ubuntu, nach der [offiziellen Anleitung](https://docs.docker.com/engine/install/ubuntu/)):

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Nicht das Ubuntu-Paket `docker.io` nehmen: Es ist älter und bringt kein `docker compose` v2 und kein Buildx mit, was viele Dev-Container-Konfigurationen erwarten.

**6.2 Docker ohne sudo nutzen.** VS Code ruft `docker` als dein Benutzer auf, deshalb muss `ed` in die Gruppe `docker`:

```bash
sudo usermod -aG docker $USER
```

Danach in PowerShell `wsl --terminate Ubuntu` und Ubuntu neu öffnen, damit die Gruppe greift.

**6.3 Proxy für den Docker-Daemon** (nur wenn Schritt 5.2 nötig war). Der Daemon läuft als systemd-Dienst und sieht deine `.bashrc` nicht:

```bash
sudo mkdir -p /etc/systemd/system/docker.service.d
sudo tee /etc/systemd/system/docker.service.d/http-proxy.conf <<'EOF'
[Service]
Environment="HTTP_PROXY=http://proxy.firma.example:8080"
Environment="HTTPS_PROXY=http://proxy.firma.example:8080"
Environment="NO_PROXY=localhost,127.0.0.1,.firma.example"
EOF
sudo systemctl daemon-reload
sudo systemctl restart docker
```

Das Firmen-Root-Zertifikat aus Schritt 5.3 nutzt der Daemon automatisch über den Ubuntu-Zertifikatsspeicher – nach dem Import einmal `sudo systemctl restart docker`.

**6.4 Proxy auch in Containern und Builds.** Damit `apt`/`npm`/`pip` innerhalb von Containern und Dockerfiles durchkommen, lege `~/.docker/config.json` an:

```json
{
  "proxies": {
    "default": {
      "httpProxy": "http://proxy.firma.example:8080",
      "httpsProxy": "http://proxy.firma.example:8080",
      "noProxy": "localhost,127.0.0.1,.firma.example"
    }
  }
}
```

**6.5 Adresskonflikte vermeiden** (optional, aber in Firmennetzen häufig). Docker nutzt standardmäßig `172.17.0.0/16` und weitere 172er-Netze. Liegen Firmenserver in diesem Bereich, sind sie aus WSL plötzlich nicht erreichbar. Frag die IT nach einem freien Bereich und setze ihn in `/etc/docker/daemon.json`:

```json
{
  "bip": "10.250.0.1/24",
  "default-address-pools": [{ "base": "10.251.0.0/16", "size": 24 }]
}
```

**6.6 Test:**

```bash
systemctl status docker --no-pager
docker run --rm hello-world
docker compose version
```

„Hello from Docker!“ heißt: Engine, Netzwerk, Proxy und Zertifikat funktionieren.

## Schritt 7: VS Code installieren und Dev Containers einrichten

VS Code läuft als Windows-Programm in der VDI. Die Erweiterung „WSL“ startet automatisch einen kleinen VS-Code-Server in Ubuntu; die Erweiterung „Dev Containers“ startet von dort aus deine Container über das Docker aus Schritt 6.

**7.1 VS Code installieren** (normales Konto). Ist VS Code schon über die Firmen-Softwareverteilung vorhanden, nimm das. Sonst eine von zwei Varianten, beide ohne Adminrechte:

| Variante | Download | Ziel | Wann |
| --- | --- | --- | --- |
| User Installer | „User Installer x64“ von [code.visualstudio.com/download](https://code.visualstudio.com/download) | `%LOCALAPPDATA%\Programs\Microsoft VS Code` | Profil ist persistent, Installer darf laufen |
| ZIP / portabel | „.zip x64“ von derselben Seite | `C:\MYSOFT\VSCode` | Profil wird zurückgesetzt oder Installer sind gesperrt |

Für die ZIP-Variante: Archiv nach `C:\MYSOFT\VSCode` entpacken, darin einen leeren Ordner `data` anlegen (aktiviert den portablen Modus: Einstellungen und Erweiterungen liegen dann ebenfalls in `C:\MYSOFT`), und `C:\MYSOFT\VSCode\bin` zum Benutzer-PATH hinzufügen (Startmenü → „Umgebungsvariablen für dieses Konto bearbeiten“). Der PATH-Eintrag ist nötig, damit `code .` später aus Ubuntu heraus funktioniert.

**7.2 Erweiterungen installieren.** In VS Code (Strg+Shift+X) suchen und installieren:

- **WSL** (`ms-vscode-remote.remote-wsl`)
- **Dev Containers** (`ms-vscode-remote.remote-containers`)

Klappt der Marketplace nicht, liegt es meist am Proxy: In den Einstellungen `http.proxy` auf deinen Proxy setzen. Notfalls die `.vsix`-Dateien im Browser herunterladen, nach `C:\MYSOFT\TEMP` legen und über „…“ → „Install from VSIX“ installieren.

**7.3 Dev Containers auf Docker in WSL einstellen.** Strg+Shift+P → „Preferences: Open User Settings (JSON)“ und ergänzen:

```json
{
  "dev.containers.executeInWSL": true,
  "dev.containers.executeInWSLDistro": "Ubuntu"
}
```

`executeInWSL` sagt der Erweiterung: Es gibt kein Docker Desktop unter Windows, führe den `docker`-Befehl in WSL aus. Das ist die entscheidende Einstellung für dein Setup.

**7.4 Projekte im Linux-Dateisystem ablegen.** Lege deinen Code unter `~/projects` in Ubuntu ab, **nicht** unter `/mnt/c/...`. Zugriffe über `/mnt/c` laufen über eine Übersetzungsschicht und sind bei vielen kleinen Dateien (`node_modules`, Git) um ein Vielfaches langsamer; zudem greift dort der Virenscanner. Da die vhdx unter `C:\MYSOFT` liegt, ist dein Code im Linux-Dateisystem trotzdem vom Scanner ausgenommen.

```bash
mkdir -p ~/projects && cd ~/projects
git clone <repo-url>
cd <repo> && code .
```

Beim ersten `code .` lädt VS Code den Server in Ubuntu herunter (Proxy aus Schritt 5 wird verwendet). Unten links steht danach „WSL: Ubuntu“.

**7.5 Git-Anmeldung (optional).** Ist Git for Windows installiert, kannst du dessen Credential Manager aus WSL mitnutzen, damit du dich nicht doppelt anmeldest:

```bash
git config --global credential.helper "/mnt/c/Program\ Files/Git/mingw64/bin/git-credential-manager.exe"
```

Dev Containers übernimmt deine `~/.gitconfig` und die Anmeldung automatisch in den Container.

## Schritt 8: Funktionstest mit einem Beispiel-Dev-Container

Ein kleines Testprojekt beweist, dass die ganze Kette funktioniert: VS Code → WSL → Docker → Container, inklusive Proxy und Firmenzertifikat.

**8.1 Testprojekt anlegen** (in Ubuntu):

```bash
mkdir -p ~/projects/devcontainer-test/.devcontainer
cd ~/projects/devcontainer-test
cp /usr/local/share/ca-certificates/firma-root.crt .devcontainer/ 2>/dev/null || true
```

**8.2 `.devcontainer/Dockerfile`** – das Firmenzertifikat wird ins Image übernommen, damit auch `apt`, `npm`, `pip` usw. im Container funktionieren:

```dockerfile
FROM mcr.microsoft.com/devcontainers/base:ubuntu
# Firmen-Root-Zertifikat (Zeilen entfernen, wenn keine TLS-Inspektion)
COPY firma-root.crt /usr/local/share/ca-certificates/firma-root.crt
RUN update-ca-certificates
# Node, Python & Co. sollen den System-Zertifikatsspeicher nutzen
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt \
    REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
```

**8.3 `.devcontainer/devcontainer.json`:**

```json
{
  "name": "WSL-Test",
  "build": { "dockerfile": "Dockerfile" },
  "features": {
    "ghcr.io/devcontainers/features/node:1": {}
  },
  "postCreateCommand": "node -v && curl -sSI https://registry.npmjs.org | head -1"
}
```

Die Proxy-Variablen musst du hier nicht eintragen: Docker übernimmt sie aus `~/.docker/config.json` (Schritt 6.4) automatisch in Build und Container.

**8.4 Starten:**

1. `code .` im Ordner `~/projects/devcontainer-test` ausführen. VS Code öffnet sich mit „WSL: Ubuntu“ unten links.
2. Strg+Shift+P → **Dev Containers: Reopen in Container**.
3. Der erste Build dauert einige Minuten (Image-Download). Mit „Show Log“ kannst du zusehen.
4. Unten links steht danach „Dev Container: WSL-Test“. Im Terminal von VS Code solltest du die Node-Version und `HTTP/2 200` aus dem `postCreateCommand` sehen.

Wenn das klappt, ist dein Setup fertig. Für echte Projekte bringen viele Repositories bereits einen `.devcontainer`-Ordner mit; dann reicht 8.4. Den Zertifikatsteil aus 8.2 musst du in firmeninternen Projekten nur einmal in deren Dockerfile übernehmen.

**Tägliche Arbeit:** VS Code starten → „Zuletzt geöffnet“ zeigt deine Container-Projekte direkt an. WSL und Docker starten dabei automatisch im Hintergrund.

## Fehlerbehebung

Die meisten Probleme in VDIs gehen auf drei Ursachen zurück: fehlende Nested Virtualization, Proxy/Zertifikat oder ein Schritt im falschen Konto.

| Symptom / Fehler | Ursache | Lösung |
| --- | --- | --- |
| `0x80370102` – VM konnte nicht gestartet werden | VMware reicht Virtualisierung nicht an die VDI durch | IT: `vhv.enable` / „Expose hardware assisted virtualization“ für die VM bzw. das Image aktivieren |
| `0x8007019e` oder „WSL-Komponente nicht installiert“ | Windows-Feature fehlt | Schritt 1 mit Admin-Konto, danach Neustart |
| `0x80370114` | Feature „VM-Plattform“ fehlt oder Hypervisor ist aus | `VirtualMachinePlatform` aktivieren; als Admin `bcdedit /enum` prüfen, ob `hypervisorlaunchtype` auf `Auto` steht |
| „WSL is disabled by your organization“ | Gruppenrichtlinie / Intune | Nur über die IT lösbar |
| `wsl -l -v` zeigt keine Distribution, obwohl installiert | Distribution wurde im Admin-Konto angelegt | Schritt 3 im normalen Konto wiederholen |
| Nach Neustart ist alles weg | Nicht-persistente VDI | Schritt 0.3; persistenten Speicher bei der IT anfragen |
| `wsl --import`: Zugriff verweigert | Keine Schreibrechte auf `C:\MYSOFT\WSL` | Rechte per `icacls` (Schritt 1) |
| „SSL certificate problem“ bei `curl`, `apt`, `docker pull` | TLS-Inspektion, Firmenzertifikat fehlt | Schritt 5.3, danach `sudo systemctl restart docker` |
| `docker pull` hängt, `curl` klappt | Daemon kennt den Proxy nicht | Schritt 6.3 |
| Build im Container scheitert beim Paket-Download | Proxy/Zertifikat fehlen im Container | Schritt 6.4 und Dockerfile aus 8.2 |
| „permission denied … /var/run/docker.sock“ | Benutzer nicht in Gruppe `docker` | Schritt 6.2, danach `wsl --terminate Ubuntu` |
| VS Code: „Docker version 17.12.0 or later is required“ / Docker nicht gefunden | Dev Containers sucht Docker unter Windows | `dev.containers.executeInWSL: true` (Schritt 7.3) |
| Firmenserver aus WSL/Container nicht erreichbar | Adresskonflikt mit 172er-Netzen | `networkingMode=mirrored` (4.1) und Docker-Adressbereich (6.5) |
| VDI wird träge, Prozess `VmmemWSL` frisst RAM | Kein Speicherlimit | `memory=` in `.wslconfig` senken, `wsl --shutdown` |
| `code .` in Ubuntu: Befehl nicht gefunden | VS-Code-`bin` nicht im Windows-PATH | PATH ergänzen (Schritt 7.1), VDI-Sitzung neu anmelden |

**Nützliche Diagnosebefehle:**

```powershell
wsl --status
wsl -l -v
wsl --shutdown          # WSL komplett neu starten
```

```bash
systemctl status docker --no-pager
journalctl -u docker --no-pager | tail -50
```

In VS Code liefert „Dev Containers: Show Container Log“ die genaue Fehlermeldung beim Container-Start.

## Was du ggf. bei der IT anfragen musst

Scheitert Schritt 0 oder 1, kommst du ohne die VDI-Administration nicht weiter. Diese Punkte kannst du gebündelt in ein Ticket schreiben – je konkreter, desto schneller:

- [ ] **Nested Virtualization** für meine VDI bzw. das Master-Image: In VMware vSphere „Expose hardware assisted virtualization to the guest OS“ aktivieren (`vhv.enable = TRUE`). Hintergrund: WSL2 benötigt die Hyper-V-basierte VM-Plattform.
- [ ] **Windows-Features** `Microsoft-Windows-Subsystem-Linux` und `VirtualMachinePlatform` aktivieren (falls mein Admin-Konto das nicht darf).
- [ ] **Persistenz**: Bleiben `C:\MYSOFT` und mein Benutzerprofil über Neustarts erhalten? Falls nein: persistenter Speicher für ca. 50 GB.
- [ ] **Ressourcen**: Mindestens 16 GB RAM und 4 vCPUs für die VDI (WSL2 plus Docker plus VS Code).
- [ ] **WSL-Richtlinie**: WSL ist nicht per Gruppenrichtlinie/Intune gesperrt.
- [ ] **Netzwerk**: Proxy-Adresse, Firmen-Root-Zertifikat (bei TLS-Inspektion) und Freigabe für `download.docker.com`, `mcr.microsoft.com`, `ghcr.io`, `github.com`, `update.code.visualstudio.com` und `marketplace.visualstudio.com`.
- [ ] **IP-Bereich**: Ein freier interner Adressbereich für Docker-Netze, der nicht mit Firmennetzen kollidiert.

> **Hinweis zu Docker Desktop:** Falls die IT stattdessen Docker Desktop vorschlägt – das ist in größeren Organisationen lizenzpflichtig. Die hier beschriebene Docker Engine in WSL ist Open Source und für Dev Containers voll ausreichend.
