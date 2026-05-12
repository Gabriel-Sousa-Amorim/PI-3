REGIONS: dict[str, dict[str, str | list[str]]] = {
    "CO": {"label": "Centro-Oeste", "states": ["GO", "MT", "MS", "DF"]},
    "N":  {"label": "Norte",        "states": ["AC", "AP", "AM", "PA", "RO", "RR", "TO"]},
    "NE": {"label": "Nordeste",     "states": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"]},
    "SE": {"label": "Sudeste",      "states": ["ES", "MG", "RJ", "SP"]},
    "S":  {"label": "Sul",          "states": ["PR", "RS", "SC"]},
}

REGIONS_CHOICES = [(code, data["label"]) for code, data in REGIONS.items()]

STATES = {
    "AC":"Acre",
    "AL":"Alagoas",
    "AM":"Amapá",
    "AP":"Amapá",
    "BA":"Bahia",
    "CE":"Ceará",
    "DF":"Distrito Federal",
    "ES":"Espírito Santo",
    "GO":"Goiás",
    "MA":"Maranhão",
    "MT":"Mato Grosso",
    "MS":"Mato Grosso do Sul",
    "MG":"Minas Gerais",
    "PA":"Pará",
    "PB":"Paraíba",
    "PR":"Paraná",
    "PE":"Pernambuco",
    "PI":"Piauí",
    "RJ":"Rio de Janeiro",
    "RN":"Rio Grande do Norte",
    "RS":"Rio Grande do Sul",
    "RO":"Rondônia",
    "RR":"Roraima",
    "SC":"Santa Catarina",
    "SP":"São Paulo",
    "SE":"Sergipe",
    "TO":"Tocantins",
}

STATE_CHOICES = [(sigla, nome) for sigla, nome in STATES.items()]