# Clivet WSAT-YSi Modbus — integracja Home Assistant

Niestandardowa integracja HA dla agregatów wody lodowej **Clivet WSAT-YSi 16.2–40.2** (R32, rebrand Midea) po **Modbus RTU / RS-485**, w praktyce przez bramkę **RS485↔TCP**.

Mapa rejestrów na podstawie oficjalnej instrukcji **Clivet M0NC00002-00 (04-2021)**, rozdział 12 „Modbus".

## Możliwości

**System (jednostka nadrzędna, zapis):**
- `climate` — tryb OFF / COOL (rejestr 0: 1=chłodzenie, 8=wył.) + nastawa temperatury wody (rejestr 1, −8…20 °C)
- `number` — nastawa temperatury B (rejestr 2)
- podgląd podwójnej nastawy i kompensacji temperatury (rejestry 101–109, tylko odczyt)

**Każda jednostka (adresy 0–15, rejestry `240+adres·100 … 293+adres·100`, tylko odczyt):**
- temperatury: Twi, Two, Tw (master), T4 zewn., tłoczenie 1/2, ssanie, T3A/T3B, Tz, T5, T6A, Taf1
- prędkość sprężarki [Hz], prądy sprężarek [A], moc [kW], prędkości wentylatorów 1–3, pozycje EXV A/B/C
- ciśnienie [kPa] (skala ×10 wg instrukcji)
- zawory SV1/SV2/SV4/SV5/SV6/SV8A/SV8B, zawór 4-drożny, pompa obiegowa, HEAT1/HEAT2, grzałka płynu niezamarzającego, zdalne sterowanie
- **kod błędu i ostatni błąd (rejestry 272/273) — automatycznie dekodowane** na kody E0…dU z opisem po polsku (tabela ze str. 39 + opisy ze str. 61–64)

## Podłączenie sprzętowe

1. RS-485 na **tylnej części sterownika przewodowego** jednostki MASTER: zaciski **H1 (−)** i **H2 (+)**.
2. Parametry łącza: **Modbus RTU, 9600 bps, 8 bitów danych, bez parzystości, 1 bit stopu**.
3. W konfiguracji modułowej Modbus podłącza się **wyłącznie do jednostki nadrzędnej (adres 0)**.
4. Aktywacja na sterowniku: przytrzymać **MENU + ►** 3 s → `SERVICE MENU > SETTING ADDRESS > MODBUS ENABLE > YES`; tam też ustawia się `MODBUS ADDRESS` (slave ID).
5. Bramka RS485↔TCP (np. Waveshare RS485 TO ETH, Elfin EW11, USR) w trybie **Modbus TCP↔RTU**, port 502.

## Instalacja

### HACS (zalecane)
HACS → Integrations → ⋮ → **Custom repositories** → dodaj `https://github.com/sebastianmorawiec1/clivet_modbus` jako *Integration* → zainstaluj → restart HA.

### Ręcznie
Skopiuj `custom_components/clivet_modbus` do katalogu `config/custom_components/` i zrestartuj HA.

## Konfiguracja

Ustawienia → Urządzenia i usługi → **Dodaj integrację** → „Clivet WSAT-YSi Modbus":

| Pole | Opis |
|---|---|
| Adres IP bramki | IP konwertera RS485↔TCP |
| Port TCP | domyślnie 502 |
| Adres Modbus | slave ID ustawiony w `SETTING ADDRESS` |
| Liczba jednostek | 1–16; dla każdej powstaje osobne urządzenie w HA |
| Interwał odpytywania | domyślnie 30 s |

## Uwagi

- Nastawa poniżej **+5 °C** wymaga glikolu etylenowego (≥10/20/30% wg zakresu roboczego z instrukcji, funkcja Tsafe). Integracja nie blokuje niskich nastaw — odpowiedzialność po stronie instalacji.
- Rejestry 101–109 wg nagłówka tabeli w instrukcji są tylko do odczytu — zapis realizowany jest wyłącznie na rejestrach 0, 1, 2.
- W tabeli kodów błędów instrukcji `FF` ma wartość 75 (dublet z `FE`) — najpewniej błąd druku; integracja mapuje `FF` na 76.
- Timery dzienny/tygodniowy jednostki są dezaktywowane, gdy sterowanie odbywa się po Modbus (str. 55 instrukcji).

## Licencja

MIT
