"""
Validadores de dados para GA4 e GSC.

Implementa validações de:
- Tipos de dados
- Ranges válidos
- Consistência entre métricas
- Anomalias
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date


class DataValidator:
    """Valida integridade e qualidade dos dados."""

    @staticmethod
    def validate_date(date_str: Any) -> Tuple[bool, Optional[str]]:
        """
        Valida formato de data.

        Args:
            date_str: String de data a validar

        Returns:
            Tuple[bool, Optional[str]]: (válido, mensagem_erro)
        """
        if date_str is None:
            return False, "Data não pode ser nula"
        
        # Aceita date objects
        if isinstance(date_str, date):
            return True, None
        
        # Valida string no formato YYYY-MM-DD
        try:
            datetime.strptime(str(date_str), "%Y-%m-%d")
            return True, None
        except ValueError:
            return False, f"Formato de data inválido: {date_str} (esperado YYYY-MM-DD)"

    @staticmethod
    def validate_positive_numeric(
        value: Any,
        field_name: str,
        allow_zero: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida que valor é numérico e positivo.

        Args:
            value: Valor a validar
            field_name: Nome do campo (para mensagem de erro)
            allow_zero: Se permite valor zero

        Returns:
            Tuple[bool, Optional[str]]: (válido, mensagem_erro)
        """
        try:
            num_value = float(value)
            
            if allow_zero:
                if num_value < 0:
                    return False, f"{field_name} não pode ser negativo: {num_value}"
            else:
                if num_value <= 0:
                    return False, f"{field_name} deve ser maior que zero: {num_value}"
            
            return True, None
        except (ValueError, TypeError):
            return False, f"{field_name} não é um número válido: {value}"

    @staticmethod
    def validate_percentage(value: Any, field_name: str) -> Tuple[bool, Optional[str]]:
        """
        Valida que valor é percentual válido (0-1).

        Args:
            value: Valor a validar
            field_name: Nome do campo

        Returns:
            Tuple[bool, Optional[str]]: (válido, mensagem_erro)
        """
        try:
            num_value = float(value)
            
            if num_value < 0 or num_value > 1:
                return False, f"{field_name} deve estar entre 0 e 1: {num_value}"
            
            return True, None
        except (ValueError, TypeError):
            return False, f"{field_name} não é um número válido: {value}"

    @staticmethod
    def validate_ctr_consistency(
        clicks: float,
        impressions: float,
        ctr: float,
        tolerance: float = 0.01
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida consistência entre clicks, impressions e CTR.

        Args:
            clicks: Número de cliques
            impressions: Número de impressões
            ctr: CTR reportado
            tolerance: Tolerância para diferença (default 1%)

        Returns:
            Tuple[bool, Optional[str]]: (válido, mensagem_erro)
        """
        if impressions == 0:
            if ctr != 0:
                return False, f"CTR deveria ser 0 quando impressions=0, mas é {ctr}"
            return True, None
        
        expected_ctr = clicks / impressions
        diff = abs(expected_ctr - ctr)
        
        if diff > tolerance:
            return False, (
                f"CTR inconsistente: esperado {expected_ctr:.4f} "
                f"(clicks={clicks}/impressions={impressions}), "
                f"mas reportado {ctr:.4f} (diferença: {diff:.4f})"
            )
        
        return True, None

    @staticmethod
    def validate_position(position: float) -> Tuple[bool, Optional[str]]:
        """
        Valida posição de busca (GSC).

        Args:
            position: Posição média

        Returns:
            Tuple[bool, Optional[str]]: (válido, mensagem_erro)
        """
        if position < 1:
            return False, f"Posição deve ser >= 1: {position}"
        
        # Alerta se posição muito alta (provável anomalia)
        if position > 1000:
            return False, f"Posição suspeita (>1000): {position}"
        
        return True, None


class GA4Validator(DataValidator):
    """Validador especializado para dados GA4."""

    @classmethod
    def validate_traffic_row(cls, row: Dict[str, Any]) -> List[str]:
        """
        Valida row de tráfego GA4.

        Args:
            row: Registro a validar

        Returns:
            List[str]: Lista de erros encontrados (vazia se válido)
        """
        errors = []
        
        # Valida data
        valid, msg = cls.validate_date(row.get("date"))
        if not valid:
            errors.append(msg)
        
        # Valida métricas numéricas
        metrics = [
            ("sessions", True),
            ("active_users", True),
            ("new_users", True),
            ("screen_page_views", True),
            ("average_session_duration", True),
        ]
        
        for metric_name, allow_zero in metrics:
            value = row.get(metric_name)
            if value is not None:
                valid, msg = cls.validate_positive_numeric(
                    value, metric_name, allow_zero
                )
                if not valid:
                    errors.append(msg)
        
        # Validação lógica: new_users <= active_users
        new_users = row.get("new_users", 0)
        active_users = row.get("active_users", 0)
        if new_users > active_users:
            errors.append(
                f"new_users ({new_users}) não pode ser maior que "
                f"active_users ({active_users})"
            )
        
        return errors

    @classmethod
    def validate_conversion_row(cls, row: Dict[str, Any]) -> List[str]:
        """
        Valida row de conversões GA4.

        Args:
            row: Registro a validar

        Returns:
            List[str]: Lista de erros encontrados
        """
        errors = []
        
        # Valida data
        valid, msg = cls.validate_date(row.get("date"))
        if not valid:
            errors.append(msg)
        
        # Valida métricas
        metrics = [
            ("key_events", True),
            ("event_count", True),
            ("total_revenue", True),
            ("transactions", True),
            ("purchase_revenue", True),
        ]
        
        for metric_name, allow_zero in metrics:
            value = row.get(metric_name)
            if value is not None:
                valid, msg = cls.validate_positive_numeric(
                    value, metric_name, allow_zero
                )
                if not valid:
                    errors.append(msg)
        
        # Validação lógica: purchase_revenue <= total_revenue
        purchase = row.get("purchase_revenue", 0)
        total = row.get("total_revenue", 0)
        if purchase > total:
            errors.append(
                f"purchase_revenue ({purchase}) não pode ser maior que "
                f"total_revenue ({total})"
            )
        
        return errors

    @classmethod
    def validate_engagement_row(cls, row: Dict[str, Any]) -> List[str]:
        """
        Valida row de engajamento GA4.

        Args:
            row: Registro a validar

        Returns:
            List[str]: Lista de erros encontrados
        """
        errors = []
        
        # Valida data
        valid, msg = cls.validate_date(row.get("date"))
        if not valid:
            errors.append(msg)
        
        # Valida engagement_rate como percentual
        engagement_rate = row.get("engagement_rate")
        if engagement_rate is not None:
            valid, msg = cls.validate_percentage(engagement_rate, "engagement_rate")
            if not valid:
                errors.append(msg)
        
        # Valida outras métricas
        metrics = [
            ("engaged_sessions", True),
            ("average_session_duration", True),
            ("event_count", True),
            ("user_engagement_duration", True),
        ]
        
        for metric_name, allow_zero in metrics:
            value = row.get(metric_name)
            if value is not None:
                valid, msg = cls.validate_positive_numeric(
                    value, metric_name, allow_zero
                )
                if not valid:
                    errors.append(msg)
        
        return errors


class GSCValidator(DataValidator):
    """Validador especializado para dados GSC."""

    @classmethod
    def validate_performance_row(
        cls,
        row: Dict[str, Any],
        check_dates: bool = True
    ) -> List[str]:
        """
        Valida row de performance GSC (genérico).

        Args:
            row: Registro a validar
            check_dates: Se deve validar start_date/end_date

        Returns:
            List[str]: Lista de erros encontrados
        """
        errors = []
        
        # Valida datas (se aplicável)
        if check_dates:
            for date_field in ["start_date", "end_date"]:
                if date_field in row:
                    valid, msg = cls.validate_date(row.get(date_field))
                    if not valid:
                        errors.append(msg)
        
        # Valida date (para date_performance)
        if "date" in row:
            valid, msg = cls.validate_date(row.get("date"))
            if not valid:
                errors.append(msg)
        
        # Valida métricas base
        clicks = row.get("clicks", 0)
        impressions = row.get("impressions", 0)
        ctr = row.get("ctr", 0)
        position = row.get("position")
        
        # Clicks
        valid, msg = cls.validate_positive_numeric(clicks, "clicks", allow_zero=True)
        if not valid:
            errors.append(msg)
        
        # Impressions
        valid, msg = cls.validate_positive_numeric(
            impressions, "impressions", allow_zero=True
        )
        if not valid:
            errors.append(msg)
        
        # CTR
        valid, msg = cls.validate_percentage(ctr, "ctr")
        if not valid:
            errors.append(msg)
        
        # Consistência CTR
        valid, msg = cls.validate_ctr_consistency(clicks, impressions, ctr)
        if not valid:
            errors.append(msg)
        
        # Position
        if position is not None:
            valid, msg = cls.validate_position(position)
            if not valid:
                errors.append(msg)
        
        # Validação lógica: clicks <= impressions
        if clicks > impressions:
            errors.append(
                f"clicks ({clicks}) não pode ser maior que "
                f"impressions ({impressions})"
            )
        
        return errors

    @classmethod
    def validate_device_value(cls, device: str) -> Tuple[bool, Optional[str]]:
        """
        Valida valor de device.

        Args:
            device: Valor de dispositivo

        Returns:
            Tuple[bool, Optional[str]]: (válido, mensagem_erro)
        """
        valid_devices = ["DESKTOP", "MOBILE", "TABLET"]
        
        if device.upper() not in valid_devices:
            return False, (
                f"Device inválido: {device} "
                f"(valores aceitos: {', '.join(valid_devices)})"
            )
        
        return True, None


class ValidationReport:
    """Gera relatórios de validação."""

    @staticmethod
    def validate_dataset(
        rows: List[Dict[str, Any]],
        validator_func: callable
    ) -> Dict[str, Any]:
        """
        Valida dataset completo e gera relatório.

        Args:
            rows: Lista de registros
            validator_func: Função de validação (retorna List[str] de erros)

        Returns:
            Dict: Relatório de validação
        """
        total_rows = len(rows)
        invalid_rows = []
        all_errors = []
        
        for idx, row in enumerate(rows):
            errors = validator_func(row)
            
            if errors:
                invalid_rows.append({
                    "row_index": idx,
                    "errors": errors,
                    "sample": row
                })
                all_errors.extend(errors)
        
        # Conta tipos de erro
        error_types = {}
        for error in all_errors:
            # Extrai tipo de erro (primeira parte antes de ":")
            error_type = error.split(":")[0] if ":" in error else error
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "total_rows": total_rows,
            "valid_rows": total_rows - len(invalid_rows),
            "invalid_rows": len(invalid_rows),
            "validation_rate": (total_rows - len(invalid_rows)) / total_rows if total_rows > 0 else 1.0,
            "error_count": len(all_errors),
            "error_types": error_types,
            "invalid_samples": invalid_rows[:5],  # Primeiras 5 rows inválidas
        }
