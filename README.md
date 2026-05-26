# Opfølgning på underskrift i forbindelse med tilbud om personlig assistance

Automatisering der følger op på manglende underskrifter i forbindelse med tilbud om personlig assistance i Momentum.

## Hvad gør robotten?

1. **Henter vitas** fra Momentum med søgetermen _"personlig assistance"_
2. **Filtrerer** på vitas uden en virksomhedsunderskriver (`companySigner`)
3. **Opretter en opgave** i Momentum til den ansvarlige sagsbehandler med en forfaldsdato 14 dage frem, der beder om opfølgning på underskriften
4. **Registrerer aktivitet** i Odense Kommunes tracking-system

## Forudsætninger

- Python ≥ 3.13
- [`uv`](https://docs.astral.sh/uv/) til pakkehåndtering
- Adgang til **Automation Server** (arbejdskø)
- Adgang til **Momentum** (produktion)
- En **Odense SQL Server**-konto til tracking

## Installation

```sh
uv sync
```

## Konfiguration

Automation Server-legitimationsoplysninger konfigureres via miljøvariabler. Kopiér `.env.example` til `.env` og udfyld:

| Variabel | Beskrivelse |
|---|---|
| _(Automation Server-variabler)_ | Ifølge `automation-server-client`-dokumentationen |

Følgende credentials skal være oprettet i Automation Server:

| Credential-navn | Beskrivelse |
|---|---|
| `Momentum - produktion` | Klientoplysninger til Momentum API (`base_url`, `client_id`, `client_secret`, `api_key`, `resource`) |
| `Odense SQL Server` | Brugernavn og adgangskode til tracking-databasen |

## Kørsel

```sh
# Fyld arbejdskøen med vitas uden underskrift
uv run python main.py --queue

# Behandl arbejdskøen (opret opgaver i Momentum)
uv run python main.py
```

### Argumenter

| Argument | Beskrivelse |
|---|---|
| `--queue` | Fyld arbejdskøen og afslut (kør ingen behandling) |

## Afhængigheder

| Pakke | Formål |
|---|---|
| `automation-server-client` | Arbejdskø-håndtering |
| `momentum-client` | Integration med Momentum |
| `odk-tools` | Aktivitetssporing |

## Persondatasikkerhed

Robotten behandler personoplysninger på vegne af Odense Kommune.

- Ingen personoplysninger må lægges i dette repository — hverken som testdata, i kode eller i kommentarer
- Legitimationsoplysninger håndteres udelukkende via miljøvariabler (`.env`) og Automation Server Credentials

