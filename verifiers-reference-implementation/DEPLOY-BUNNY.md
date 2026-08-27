# Deployment auf Bunny Magic Containers

Ziel: `https://digital-id-verifier.b-cdn.net/` wird vom Python-Verifier bedient, der als
Magic-Containers-App auf dem Bunny-Edge läuft (statt wie bisher auf dem k8s-Cluster
`k8s-hall`, Namespace `digital-id-verifier-prd`).

## Architektur

```
Browser / Wallet
      |
      v
digital-id-verifier.b-cdn.net      Pull Zone 5738993 (bleibt bestehen)
      |  Origin URL
      v
mc-<hash>.bunny.run                CDN-Endpoint der Magic-Containers-App
      |
      v
Container halltabak/digital-id-verifier:<sha>   gunicorn :5001
```

Der `b-cdn.net`-Hostname gehoert fest zum Pull-Zone-Namen und kann nicht auf eine App
umgehaengt werden. Magic Containers vergibt fuer einen CDN-Endpoint immer eine
`mc-<hash>.bunny.run`-URL. Deshalb bleibt die bestehende Pull Zone stehen und bekommt
lediglich eine neue Origin-URL.

## 1. Image bauen und pushen

Magic Containers unterstuetzt **ausschliesslich `linux/amd64`**.

```bash
make push-mc            # baut linux/amd64, pusht :<git-sha> und :latest
```

Immer den unveraenderlichen Tag in der App eintragen, nicht `latest` — sonst ist nicht
nachvollziehbar, welcher Stand laeuft, und Rollbacks sind Raterei.

Der Build laeuft mit `--provenance=false --sbom=false`, damit im Registry ein schlichtes
Single-Arch-Manifest liegt statt eines OCI-Index mit `unknown/unknown`-Attestation.

Aktuell gepusht und getestet:

```
halltabak/digital-id-verifier:mc-20260827-be9ce64
sha256:5aeede96b0b84d67b965930a23bf7d17b4e551f308d2cdc4891d86e221b499a7
```

## Lokal testen

```bash
make up          # docker compose, http://localhost:5001
make down
```

## 2. Registry in Bunny hinterlegen (einmalig)

`halltabak/digital-id-verifier` ist ein privates Docker-Hub-Repo.

Magic Containers → **Image Registries** → **Add Image Registry**:
- Type: Docker
- Username: `halltabak`
- Token: Docker-Hub Personal Access Token mit **Read-only**

## 3. App anlegen

Magic Containers → **Add App** → *Single region* (oder *Magic deployment*).

- Region: naechstgelegene EU-Region
- Container: `halltabak/digital-id-verifier:mc-20260827-be9ce64` aus der obigen Registry
- Endpoint: **CDN**, Container-Port `5001`, *SSL for origin* **aus**
  (im Container laeuft plain HTTP; TLS terminiert Bunny)
- Health Checks (Container Settings → Monitoring): Readiness **und** Liveness,
  HTTP GET auf `/healthz`, Port `5001`
- Environment Variables (optional, ueberschreiben `config.py`):
  `APP_PACKAGE_NAME`, `ANDROID_APP_SIGNATURE_HASH`, `ZK_VERIFIER_URL`, `SPECS_URL`,
  `PORT` (Default 5001)

Danach steht die Endpoint-URL `mc-<hash>.bunny.run` im Tab **Endpoints**. Erst dagegen
testen:

```bash
curl -i https://mc-<hash>.bunny.run/healthz
curl -X POST -H 'Content-Type: application/json' -d '{}' https://mc-<hash>.bunny.run/request
```

## 4. Pull Zone umbiegen

CDN → Pull Zone `digital-id-verifier` (ID 5738993) → **Origin**:

- Origin URL: `https://mc-<hash>.bunny.run`
- Host-Header: leer lassen (wird aus der Origin-URL abgeleitet)

Danach Cache leeren, sonst wird die alte, bis zu 30 Tage gecachte Startseite
weiter ausgeliefert:

```bash
BUNNY_API_KEY=... make purge-cdn
```

## 5. Alte Deployment-Wege

Erst abschalten, wenn Schritt 4 verifiziert ist:

```bash
helm uninstall digital-id-verifier -n digital-id-verifier-prd --kube-context admin@k8s-hall
```

Chart und Makefile-Targets (`install`, `template`, `lint`) bleiben als Fallback im Repo.

## Betriebshinweise

- **Cache:** Die Pull Zone cached `GET /` aggressiv. Nach jedem Deploy purgen.
  Die API-Endpoints (`POST /request`, `POST /verify`) sind davon nicht betroffen.
- **Zustand:** Der Verifier ist zustandslos — Nonce und JWE-Private-Key gehen im
  `state`-Objekt zum Client zurueck und kommen mit `/verify` wieder herein. Mehrere
  Instanzen und Regionen sind daher unproblematisch, Sticky Sessions unnoetig.
- **Kosten:** Magic Containers rechnet pro Instanz-Stunde und Region ab. Mit einer
  Region und einer Instanz starten.
