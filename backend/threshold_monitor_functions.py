def check_thresholds_and_create_alerts(metric_type: str, current_value: float, device_id: int = None):
    """
    Verifica se algum threshold foi violado e cria alertas apropriados.

    Args:
        metric_type: Tipo da métrica ('cpu', 'ram', 'disk', etc.)
        current_value: Valor atual da métrica
        device_id: ID do dispositivo (opcional)
    """
    try:
        import crud_alert_thresholds

        db = database.SessionLocal()

        # Verifica violações de threshold
        violations = crud_alert_thresholds.check_threshold_violation(
            db, metric_type, current_value, device_id
        )

        # Cria alertas para cada violação
        for violation in violations:
            # Determina severidade baseada no tipo de violação
            severity = 'medium'
            if violation['metric_type'] in ['cpu', 'ram'] and current_value > 90:
                severity = 'high'
            elif violation['metric_type'] == 'disk' and current_value > 95:
                severity = 'critical'

            # Cria o alerta
            alert_title = f'Alerta de {violation["metric_type"].upper()}'
            alert_message = f'Valor {current_value} {violation["comparison"]} {violation["threshold_value"]} (Threshold ID: {violation["threshold_id"]})'

            create_system_alert(
                title=alert_title,
                message=alert_message,
                alert_type='warning',
                severity=severity,
                source='threshold_monitor',
                device_id=device_id,
                alert_metadata={
                    'threshold_id': violation['threshold_id'],
                    'metric_type': violation['metric_type'],
                    'threshold_value': violation['threshold_value'],
                    'current_value': current_value,
                    'comparison': violation['comparison']
                }
            )

        db.close()

    except Exception as e:
        print(f'[THRESHOLD MONITOR][ERRO] Falha ao verificar thresholds: {e}')

def monitor_system_metrics(device_data: dict, device_id: int = None):
    """
    Monitora métricas do sistema e verifica thresholds.

    Args:
        device_data: Dados do dispositivo coletados
        device_id: ID do dispositivo
    """
    try:
        # CPU Usage
        if 'cpu_usage' in device_data:
            check_thresholds_and_create_alerts('cpu', device_data['cpu_usage'], device_id)

        # RAM Usage
        if 'ram_usage_percent' in device_data:
            check_thresholds_and_create_alerts('ram', device_data['ram_usage_percent'], device_id)

        # Disk Usage
        if 'disk_usage' in device_data:
            for disk in device_data['disk_usage']:
                if 'usage_percent' in disk:
                    check_thresholds_and_create_alerts('disk', disk['usage_percent'], device_id)

        # Temperature
        if 'temperatures' in device_data:
            for temp_data in device_data['temperatures']:
                if 'value' in temp_data:
                    check_thresholds_and_create_alerts('temperature', temp_data['value'], device_id)

        # Battery
        if 'battery' in device_data and 'percent' in device_data['battery']:
            check_thresholds_and_create_alerts('battery', device_data['battery']['percent'], device_id)

    except Exception as e:
        print(f'[SYSTEM MONITOR][ERRO] Falha ao monitorar métricas: {e}')
