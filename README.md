# idebo

Jednoduchý terminálový program pro zobrazení odjezdů z `mpvnet.cz`.

## Instalace na Linuxu

Instalace do uživatelského adresáře (bez `sudo`):

```bash
curl -sSfL https://raw.githubusercontent.com/kralicekgamer/idebo/main/install.sh | bash
```

Instalační skript vytvoří venv v `~/.local/share/idebo` a příkaz `idebo` v
`~/.local/bin`. Pro lokální checkout lze použít `python3 -m pip install .`.

Odinstalace:

```bash
curl -sSfL https://raw.githubusercontent.com/kralicekgamer/idebo/main/uninstall.sh | bash
```

## Konfigurace

První konfiguraci vytvoří:

```bash
idebo init
```

Výchozí soubor je `~/.config/idebo/config.ini`. Lze použít také `IDEBO_CONFIG`,
`--config` nebo kompatibilní `config.ini` v aktuálním adresáři.

```ini
[Config]
Operator = idol
HomeStop = 53289
NumberOfConnections = 5
Timeout = 10
Retries = 2
```

Podporovaní dopravci jsou `pid`, `idol`, `odis`, `zlin` a `jikord`.

## Použití

Bez argumentů se zobrazí odjezdy z konfigurace:

```bash
idebo
```

Jednorázové přepsání konfigurace:

```bash
idebo --stop 53289 --operator idol --limit 10
```

Vyhledání zastávky:

```bash
idebo search "Janův Důl" --operator idol
```

Výsledky odjezdů i vyhledávání lze získat jako JSON pomocí `--json`. Barvy se
automaticky vypínají při přesměrování výstupu; ručně je lze vypnout přes
`--no-color`.

## Chyby a síť

Dočasné timeouty, chyby připojení a HTTP chyby serveru 5xx se opakují podle
`Retries`. Neplatná konfigurace, vstup nebo odpověď API se nikdy tiše
neignoruje a program skončí s nenulovým návratovým kódem.
