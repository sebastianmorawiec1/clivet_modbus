"""Stałe integracji Clivet WSAT-YSi Modbus.

Mapa rejestrów wg instrukcji Clivet M0NC00002-00 (04-2021), rozdział 12 MODBUS.
Protokół: Modbus RTU 9600,8,N,1 przez RS-485 (port H1-/H2+ z tyłu sterownika),
w praktyce przez bramkę RS485<->TCP (Modbus TCP lub RTU-over-TCP po stronie bramki).

Jednostka modułowa: Modbus podłącza się do jednostki nadrzędnej (MASTER, adres 0).
Rejestry jednostek: bazowy_rejestr + (adres_jednostki * 100), tylko odczyt.
"""

DOMAIN = "clivet_modbus"

CONF_SLAVE = "slave"
CONF_UNITS = "units"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_PORT = 502
DEFAULT_SLAVE = 1
DEFAULT_UNITS = 1
DEFAULT_SCAN_INTERVAL = 30

MANUFACTURER = "Clivet"
MODEL = "WSAT-YSi 16.2-40.2"

# --- Rejestry systemowe (odczyt/zapis wg instrukcji, str. 35) ---
REG_MODE = 0          # 1 = Chłodzenie, 8 = Wył.
REG_SETPOINT = 1      # od -8 (lub Tsafe) do 20 °C
REG_SETPOINT_B = 2    # od -8 (lub Tsafe) do 20 °C

MODE_COOL = 1
MODE_OFF = 8

# --- Rejestry 101-113 (str. 36) — traktowane jako tylko-odczyt ---
SYSTEM_SENSORS = [
    # (rejestr, klucz, nazwa, jednostka, signed, binary)
    (101, "double_setpoint", "Podwójna wartość zadana", None, False, True),
    (102, "setpoint_cool_1", "Wartość zadana chłodzenia 1", "°C", True, False),
    (103, "setpoint_cool_2", "Wartość zadana chłodzenia 2", "°C", True, False),
    (106, "temp_compensation", "Kompensacja temperatury", None, False, True),
    (107, "temp_comp_point_1", "Kompensacja - punkt 1", "°C", True, False),
    (108, "temp_comp_point_2", "Kompensacja - punkt 2", "°C", True, False),
    (109, "temp_comp_value", "Kompensacja - wartość", "°C", True, False),
]
SYSTEM_BLOCK_START = 101
SYSTEM_BLOCK_COUNT = 9  # 101..109

# --- Blok jednostki: rejestr bazowy + adres*100 (str. 36-38), tylko odczyt ---
UNIT_BLOCK_START = 240
UNIT_BLOCK_COUNT = 54  # 240..293

MODE_MAP = {1: "zatrzymanie", 2: "chłodzenie", 3: "nieużywany"}
SILENT_MAP = {1: "standard", 2: "cichy", 3: "super cichy"}

# (rejestr, klucz, nazwa, jednostka, device_class, signed, skala, enum)
UNIT_SENSORS = [
    (240, "operating_mode", "Tryb pracy", None, None, False, 1, MODE_MAP),
    (241, "silent_mode", "Tryb cichy", None, None, False, 1, SILENT_MAP),
    (244, "twi", "Twi temperatura wody na wlocie", "°C", "temperature", True, 1, None),
    (245, "two", "Two temperatura wody na wylocie", "°C", "temperature", True, 1, None),
    (246, "tw", "Tw całkowita temperatura na wylocie", "°C", "temperature", True, 1, None),
    (247, "t4_outdoor", "T4 temperatura zewnętrzna", "°C", "temperature", True, 1, None),
    (248, "compressor_speed", "Prędkość sprężarki", "Hz", "frequency", False, 1, None),
    (249, "unit_current", "Prąd jednostki", "A", "current", False, 1, None),
    (250, "fan_speed_1", "Prędkość wentylatora 1", "rpm", None, False, 1, None),
    (251, "fan_speed_2", "Prędkość wentylatora 2", "rpm", None, False, 1, None),
    (252, "fan_speed_3", "Prędkość wentylatora 3", "rpm", None, False, 1, None),
    (253, "exv_a", "EXVA pozycja", None, None, False, 1, None),
    (254, "exv_b", "EXVB pozycja", None, None, False, 1, None),
    (255, "exv_c", "EXVC pozycja", None, None, False, 1, None),
    (266, "discharge_temp_1", "Temperatura tłoczenia 1", "°C", "temperature", True, 1, None),
    (267, "suction_temp", "Temperatura ssania", "°C", "temperature", True, 1, None),
    (268, "t3a", "Temperatura T3A", "°C", "temperature", True, 1, None),
    (269, "tz", "Temperatura Tz", "°C", "temperature", True, 1, None),
    (270, "t5", "Temperatura T5", "°C", "temperature", True, 1, None),
    (271, "pressure", "Ciśnienie", "kPa", "pressure", False, 10, None),
    (274, "sw_version_hmi", "Wersja oprogramowania HMI", None, None, False, 1, None),
    (275, "discharge_temp_2", "Temperatura tłoczenia 2", "°C", "temperature", True, 1, None),
    (276, "t3b", "Temperatura T3B", "°C", "temperature", True, 1, None),
    (277, "t6a", "Temperatura T6A", "°C", "temperature", True, 1, None),
    (280, "compressor_2_current", "Prąd sprężarki 2", "A", "current", False, 1, None),
    (281, "unit_power", "Moc jednostki", "kW", "power", False, 1, None),
    (289, "safety_temp", "Temperatura bezpieczeństwa", "°C", "temperature", True, 1, None),
    (290, "min_safety_pressure", "Minimalne ciśnienie bezpieczeństwa", "kPa", "pressure", False, 10, None),
    (291, "taf1", "Taf1 temperatura wlotu BPHE", "°C", "temperature", True, 1, None),
    (292, "sw_version_board", "Wersja oprogramowania płyty", None, None, False, 1, None),
    (293, "eeprom_version", "Wersja EEPROM", None, None, False, 1, None),
]

# Rejestr 246 (Tw) jest ważny tylko dla jednostki nadrzędnej (adres 0)
MASTER_ONLY_REGS = {246}

# (rejestr, klucz, nazwa, device_class)
UNIT_BINARY_SENSORS = [
    (256, "sv4", "SV4", None),
    (257, "sv5", "SV5", None),
    (258, "sv8a", "SV8A", None),
    (259, "sv8b", "SV8B", None),
    (260, "four_way_valve", "Zawór 4-drożny", None),
    (261, "pump", "Pompa obiegowa", "running"),
    (262, "sv1", "SV1", None),
    (263, "sv2", "SV2", None),
    (264, "heat1", "HEAT1", "heat"),
    (265, "heat2", "HEAT2", "heat"),
    (279, "sv6", "SV6", None),
    (283, "antifreeze_heater", "Grzałka płynu niezamarzającego", "heat"),
    (284, "remote_control", "Zdalne sterowanie", None),
]

REG_ERROR = 272
REG_LAST_ERROR = 273

# --- Tabela kodów błędów (str. 39) ---
# Rejestr zwraca wartość dziesiętną (młodszy bajt); liczą się 2 ostatnie znaki kodu.
_ERROR_ROWS: list[tuple[list[str], list[int]]] = [
    (["E0", "E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8", "E9", "EA", "Eb", "EC", "Ed", "EE"],
     list(range(1, 16))),
    (["EF", "EH", "EL", "EP", "EU", "P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9"],
     list(range(16, 31))),
    (["PA", "Pb", "PC", "Pd", "PE", "PF", "PH", "PL", "PP", "PU", "H0", "H1", "H2", "H3", "H4"],
     list(range(31, 46))),
    (["H5", "H6", "H7", "H8", "H9", "HA", "Hb", "HC", "Hd", "HE", "HF", "HH", "HL", "HP", "HU"],
     list(range(46, 61))),
    (["F0", "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "FA", "Fb", "Fc", "Fd", "FE"],
     list(range(61, 76))),
    # Uwaga: w instrukcji FF ma wartość 75 (dublet z FE) - prawdopodobnie błąd druku (powinno być 76).
    (["FF", "FH", "FL", "FP", "FU", "C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"],
     [76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90]),
    (["CA", "Cb", "CC", "Cd", "CE", "CF", "CH", "CL", "CP", "CU", "L0", "L1", "L2", "L3", "L4"],
     list(range(91, 106))),
    (["L5", "L6", "L7", "L8", "L9", "LA", "Lb", "LC", "Ld", "LE", "LF", "LH", "LL", "LP", "LU"],
     list(range(106, 121))),
    (["d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7", "d8", "d9", "dA", "db", "dC", "dd", "dE"],
     list(range(131, 146))),
    (["dF", "dH", "dL", "dP", "dU"],
     list(range(146, 151))),
]

ERROR_CODES: dict[int, str] = {}
for _codes, _decs in _ERROR_ROWS:
    for _c, _d in zip(_codes, _decs):
        ERROR_CODES[_d] = _c

# Opisy najważniejszych kodów (str. 61-64)
ERROR_DESCRIPTIONS: dict[str, str] = {
    "E0": "Błąd EEPROM",
    "E1": "Sekwencja faz (płyta główna)",
    "E2": "Błąd komunikacji płyta główna - klawiatura",
    "E3": "Usterka czujnika Tw (jednostka nadrzędna)",
    "E4": "Usterka czujnika Two",
    "E7": "Usterka czujnika T4",
    "E8": "Sekwencja faz",
    "E9": "Brak przepływu wody (reset ręczny)",
    "Eb": "Usterka czujnika płynu niezamarzającego Taf",
    "EC": "Redukcja modułu jednostki podrzędnej",
    "Ed": "Sonda temperatury odpływu sprężarki",
    "EE": "Czujnik temperatury T6A/T6B",
    "EF": "Czujnik temperatury powrotu wody",
    "EH": "Błąd samokontroli",
    "EP": "Sonda temperatury spuszczania (Pc>=3,5 MPa / Tz>=56C)",
    "EU": "Czujnik całkowitej temperatury skraplacza Tz",
    "P0": "Wysokie ciśnienie / temperatura odpływu",
    "P1": "Niskie ciśnienie",
    "P2": "Wysoka całkowita temperatura na wyjściu sprężarki Tz",
    "P4": "Sprężarka w trybie ochronnym",
    "P6": "Błąd modułu",
    "P7": "Wysoka temperatura skraplacza",
    "P9": "Różnica temperatury wody wlot/wylot (sprawdzić przepływ)",
    "Pb": "Zabezpieczenie przeciwzamrożeniowe (zima)",
    "PC": "Niskie ciśnienie parownika w chłodzeniu",
    "PE": "Niska temperatura parownika (ochrona przeciwzamrożeniowa)",
    "PF": "Blokada płytki drukowanej",
    "PH": "Wysoka temperatura T4",
    "PL": "Wysoka temperatura modułu Tfin",
    "PP": "Błąd modułu IPM",
    "PU": "Moduł wentylatora",
    "H5": "Wysokie / niskie napięcie",
    "H9": "Sterownik sprężarki - błąd konfiguracji",
    "HE": "Błąd zaworu",
    "F0": "Błąd transmisji modułu IPM",
    "F2": "Niewystarczające przegrzanie",
    "F3": "Błąd transmisji wentylatora",
    "F4": "Zabezpieczenie L0/L1 3 razy w 60 minut",
    "F6": "Napięcie szyny (PTC)",
    "F9": "Czujnik temperatury chłodnicy Tfin",
    "Fb": "Czujnik ciśnienia (<0,3 MPa w 15 min od startu)",
    "Fd": "Czujnik temperatury powrotu powietrza",
    "FE": "Czujnik temperatury odzyskiwania",
    "FF": "Wentylator",
    "FP": "Błąd konfiguracji DIP jednostki modułowej",
    "C7": "3 razy PL",
    "L0": "Zabezpieczenie modułu",
    "L1": "Niskie napięcie",
    "L2": "Wysokie napięcie",
    "L4": "Błąd MCE",
    "L5": "Prędkość 0",
    "L7": "Brak fazy",
    "L8": "Wahanie częstotliwości > 15 Hz",
    "L9": "Różnica częstotliwości faz > 15 Hz",
    "d0": "Błąd bramki",
    "dF": "Odmrażanie",
}


def decode_error(value: int | None) -> str:
    """Zdekoduj wartość rejestru 272/273 na kod błędu z opisem."""
    if value is None:
        return "brak danych"
    v = value & 0xFF  # tylko młodszy bajt
    if v == 0:
        return "OK"
    code = ERROR_CODES.get(v)
    if code is None:
        return f"nieznany ({v})"
    desc = ERROR_DESCRIPTIONS.get(code)
    return f"{code} - {desc}" if desc else code
