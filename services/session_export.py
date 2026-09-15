"""
Exportação do resultado de uma sessão de diagnóstico para ficheiro,
para o mecânico poder arquivar ou entregar ao cliente/oficina.
"""

import csv
import json
from datetime import datetime


def export_dtcs_csv(path, vehicle, dtcs):

    with open(path, "w", newline="", encoding="utf-8") as file:

        writer = csv.writer(file)

        writer.writerow(["Roots Auto Doctor — Relatório de Códigos de Falha"])
        writer.writerow(["Gerado em", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(["VIN", vehicle.get("vin") or "—"])
        writer.writerow(["Veículo", vehicle.get("label") or "—"])
        writer.writerow([])
        writer.writerow(["Código", "Categoria", "Origem", "Estado", "Descrição"])

        for dtc in dtcs:
            writer.writerow([
                dtc.code,
                dtc.category,
                dtc.origin_label,
                dtc.status,
                dtc.description,
            ])


def export_session_json(path, vehicle, dtcs, live_snapshot=None):

    data = {
        "gerado_em": datetime.now().isoformat(),
        "veiculo": vehicle,
        "codigos_falha": [
            {
                "codigo": dtc.code,
                "categoria": dtc.category,
                "origem": dtc.origin_label,
                "estado": dtc.status,
                "descricao": dtc.description,
            }
            for dtc in dtcs
        ],
        "dados_em_tempo_real": live_snapshot or {},
    }

    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def export_live_data_csv(path, samples):
    """Exporta uma gravação de Dados em Tempo Real para CSV.

    'samples' é uma lista de dicts com as chaves:
        tempo (str), parametro (str), valor, unidade (str)
    tal como acumulados durante uma sessão de leitura ao vivo.
    """

    with open(path, "w", newline="", encoding="utf-8") as file:

        writer = csv.writer(file)

        writer.writerow(["Roots Auto Doctor — Gravação de Dados em Tempo Real"])
        writer.writerow(["Gerado em", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow([])
        writer.writerow(["Tempo", "Parâmetro", "Valor", "Unidade"])

        for sample in samples:
            writer.writerow([
                sample.get("tempo"),
                sample.get("parametro"),
                sample.get("valor"),
                sample.get("unidade"),
            ])
