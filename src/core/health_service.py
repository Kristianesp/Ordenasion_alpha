#!/usr/bin/env python3
"""
Servicio de Salud de Discos
Calcula puntuaciones y factores de salud basados en datos SMART
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from src.utils.app_config import AppConfig
from src.utils.constants import EMOJI, HEALTH_LABELS


@dataclass
class HealthResult:
    """Resultado del análisis de salud de un disco"""
    score: int
    status: str
    factors: list
    temp_score: int
    tbw_score: int
    hours_score: int
    cycles_score: int
    device_type: str
    temperature: Optional[int]
    power_on_hours: Optional[int]
    power_cycles: Optional[int]
    tbw: Dict[str, Any]


class HealthService:
    """Servicio para calcular salud de discos basado en datos SMART"""
    
    def __init__(self, app_config: Optional[AppConfig] = None):
        self.app_config = app_config or AppConfig()
    
    def calculate_health(self, smart_data: Dict[str, Any], disk_info: Any) -> HealthResult:
        """
        Calcula la salud de un disco basado en datos SMART
        
        Args:
            smart_data: Datos SMART del disco
            disk_info: Información del disco (DiskInfo)
            
        Returns:
            HealthResult con puntuación y factores
        """
        factors = []
        device_type = smart_data.get('device_type') or 'unknown'
        
        # Cargar configuración de salud
        health_cfg = self.app_config.get("health", {})
        temp_cfg = health_cfg.get("temperature", {})
        tbw_per_tb = float(health_cfg.get("tbw_per_tb", 150))
        tbw_bands = health_cfg.get("tbw_bands", {"medium": 0.5, "high": 0.8})
        hours_bands = health_cfg.get("hours_bands", {"moderate": 10000, "high": 30000, "very_high": 50000})
        cycles_bands = health_cfg.get("cycles_bands", {"moderate": 2000, "high": 10000})
        weights = health_cfg.get("weights", {"temp": 0.35, "tbw": 0.35, "hours": 0.20, "cycles": 0.10})
        tbw_by_type = health_cfg.get("tbw_by_type", {})
        degrade_on_smart_fail = bool(health_cfg.get("degrade_on_smart_fail", True))
        
        # 1) Temperatura
        temp = smart_data.get('temperature')
        temp_score = 100
        if temp is not None:
            t_crit = int(temp_cfg.get("critical", 85))
            t_high = int(temp_cfg.get("high", 75))
            t_mod = int(temp_cfg.get("moderate", 65))
            t_cool = int(temp_cfg.get("cool_min", 40))
            if temp < 0 or temp >= t_crit:
                temp_score = 10; factors.append(f"{EMOJI['red']} {HEALTH_LABELS['critical']}: Temperatura fuera de rango (≥{t_crit}°C o <0°C)")
            elif temp >= t_high:
                temp_score = 40; factors.append(f"{EMOJI['orange']} ALTA: Temperatura ≥{t_high}°C (reduce vida)")
            elif temp >= t_mod:
                temp_score = 70; factors.append(f"{EMOJI['yellow']} MODERADA: Temperatura {t_mod}-{t_high-1}°C")
            elif temp >= t_cool:
                temp_score = 95; factors.append(f"{EMOJI['green']} ÓPTIMA: Temperatura {t_cool}-{t_mod-1}°C")
            else:
                temp_score = 90; factors.append(f"{EMOJI['green']} FRÍA: Temperatura <40°C")
        else:
            factors.append(f"{EMOJI['info']} Temperatura no reportada")

        # 2) Desgaste por TBW
        read_tb = (smart_data.get('read_bytes') or 0) / 1024**4
        write_tb = (smart_data.get('write_bytes') or 0) / 1024**4
        total_tbw = read_tb + write_tb
        capacity_tb = max(1.0, disk_info.total_size / (1024**4))
        rated_tbw = float(tbw_per_tb) * capacity_tb
        
        # Ajuste por tipo
        if device_type in tbw_by_type:
            rated_tbw = float(tbw_by_type.get(device_type, tbw_per_tb)) * capacity_tb
        if device_type == 'hdd':
            # Ignorar TBW en HDD si está configurado a 0
            if float(tbw_by_type.get('hdd', 0)) == 0:
                rated_tbw = 0.0
        
        usage_ratio = total_tbw / rated_tbw if rated_tbw > 0 else 0
        tbw_score = 100
        if rated_tbw == 0:
            # No penalizar TBW cuando no aplica (p.ej., HDD)
            tbw_score = 100; factors.append(f"{EMOJI['info']} TBW no aplica para este dispositivo")
        elif usage_ratio >= 1.0:
            tbw_score = 10; factors.append(f"{EMOJI['red']} TBW excedido ({total_tbw:.0f}TB de {rated_tbw:.0f}TB)")
        elif usage_ratio >= float(tbw_bands.get("high", 0.8)):
            tbw_score = 40; factors.append(f"{EMOJI['orange']} TBW alto (≥{int(tbw_bands.get('high', 0.8)*100)}%: {total_tbw:.0f}/{rated_tbw:.0f}TB)")
        elif usage_ratio >= float(tbw_bands.get("medium", 0.5)):
            tbw_score = 70; factors.append(f"{EMOJI['yellow']} TBW medio (≥{int(tbw_bands.get('medium', 0.5)*100)}%: {total_tbw:.0f}/{rated_tbw:.0f}TB)")
        else:
            tbw_score = 100; factors.append(f"{EMOJI['green']} TBW bajo ({total_tbw:.0f}/{rated_tbw:.0f}TB)")

        # 3) Horas de encendido
        hours = smart_data.get('power_on_hours') or 0
        hours_score = 100
        h_vhigh = int(hours_bands.get("very_high", 50000))
        h_high = int(hours_bands.get("high", 30000))
        h_mod = int(hours_bands.get("moderate", 10000))
        if hours >= h_vhigh:
            hours_score = 40; factors.append(f"{EMOJI['orange']} MUY USADO: ≥50.000h")
        elif hours >= h_high:
            hours_score = 70; factors.append(f"{EMOJI['yellow']} USO ALTO: 30.000-49.999h")
        elif hours >= h_mod:
            hours_score = 90; factors.append(f"{EMOJI['green']} USO MODERADO: 10.000-29.999h")
        else:
            hours_score = 100; factors.append(f"{EMOJI['green']} BAJO USO: <10.000h")

        # 4) Ciclos de encendido
        cycles = smart_data.get('power_cycles') or 0
        cycles_score = 100
        c_high = int(cycles_bands.get("high", 10000))
        c_mod = int(cycles_bands.get("moderate", 2000))
        if cycles >= c_high:
            cycles_score = 60; factors.append(f"{EMOJI['yellow']} Ciclos de encendido muy altos (≥10.000)")
        elif cycles >= c_mod:
            cycles_score = 85; factors.append(f"{EMOJI['green']} Ciclos moderados (2.000-9.999)")
        else:
            cycles_score = 100; factors.append(f"{EMOJI['green']} Ciclos bajos (<2.000)")

        # 5) Operaciones (informativo)
        read_count = smart_data.get('read_count') or 0
        write_count = smart_data.get('write_count') or 0
        factors.append(f"{EMOJI['info']} Operaciones: {read_count:,} lecturas, {write_count:,} escrituras")

        # Pesos
        w_temp = float(weights.get('temp', 0.35))
        w_tbw = float(weights.get('tbw', 0.35))
        w_hours = float(weights.get('hours', 0.20))
        w_cycles = float(weights.get('cycles', 0.10))

        score = (
            temp_score * w_temp +
            tbw_score * w_tbw +
            hours_score * w_hours +
            cycles_score * w_cycles
        )

        # Degradar estado si SMART indica fallo
        smart_passed = smart_data.get('smart_status', True)
        if degrade_on_smart_fail and not smart_passed:
            factors.append(f"{EMOJI['red']} SMART REPORTA FALLO: Prioriza respaldo y reemplazo")
            score = min(score, 59)  # Forzar al menos ATENCIÓN

        # Estado final
        if score >= 90:
            status = f"{EMOJI['green']} {HEALTH_LABELS['excellent']} - Mantén el buen uso del disco"
        elif score >= 75:
            status = f"{EMOJI['green']} {HEALTH_LABELS['healthy']} - Monitorea regularmente"
        elif score >= 60:
            status = f"{EMOJI['yellow']} {HEALTH_LABELS['attention']} - Revisa ventilación/uso, backups al día"
        elif score >= 40:
            status = f"{EMOJI['orange']} {HEALTH_LABELS['warning']} - Considera reemplazo preventivo y backups"
        else:
            status = f"{EMOJI['red']} {HEALTH_LABELS['critical']} - Reemplazo recomendado"

        return HealthResult(
            score=int(round(score)),
            status=status,
            factors=factors,
            temp_score=temp_score,
            tbw_score=tbw_score,
            hours_score=hours_score,
            cycles_score=cycles_score,
            device_type=device_type,
            temperature=temp if temp is not None else None,
            power_on_hours=hours,
            power_cycles=cycles,
            tbw={
                "read_tb": round(read_tb, 1),
                "write_tb": round(write_tb, 1),
                "rated_tbw": int(rated_tbw)
            }
        )
