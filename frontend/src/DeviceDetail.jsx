import React from 'react';
import './DeviceDetail.css';

function DeviceDetail({ device, onClose }) {
  if (!device) return null;

  // Helper function to check if an object has any non-null properties
  const hasData = (obj) => {
    if (!obj) return false;
    return Object.values(obj).some(value => value !== null && value !== undefined);
  };

  // Helper function to format values for display
  const formatValue = (value) => {
    if (value === null || value === undefined) return 'N/A';
    if (typeof value === 'boolean') return value ? 'Sim' : 'Não';
    if (typeof value === 'number') return value.toString();
    return value;
  };

  return (
    <div className="device-detail-overlay">
      <div className="device-detail-container">
        <div className="device-detail-header">
          <h2>{device.name || 'Dispositivo'} - Detalhes de Hardware</h2>
          <button className="close-button" onClick={onClose}>×</button>
        </div>

        <div className="device-detail-content">
          <div className="device-basic-info">
            <h3>Informações Básicas</h3>
            <table>
              <tbody>
                <tr>
                  <td>Nome:</td>
                  <td>{device.name || 'N/A'}</td>
                </tr>
                <tr>
                  <td>Endereço IP:</td>
                  <td>{device.ip_address}</td>
                </tr>
                <tr>
                  <td>Endereço MAC:</td>
                  <td>{device.mac_address || 'N/A'}</td>
                </tr>
                <tr>
                  <td>Tipo:</td>
                  <td>{device.device_type}</td>
                </tr>
                <tr>
                  <td>Sistema Operacional:</td>
                  <td>{device.os || 'N/A'}</td>
                </tr>
                <tr>
                  <td>Status:</td>
                  <td>{device.status}</td>
                </tr>
                <tr>
                  <td>Última Visualização:</td>
                  <td>{new Date(device.last_seen).toLocaleString()}</td>
                </tr>
              </tbody>
            </table>
          </div>

          {device.hardware_details ? (
            <div className="hardware-details">
              {/* CPU Information */}
              {hasData(device.hardware_details.cpu_info) && (
                <div className="detail-section">
                  <h3>Processador (CPU)</h3>
                  <table>
                    <tbody>
                      <tr>
                        <td>Fabricante:</td>
                        <td>{formatValue(device.hardware_details.cpu_info.brand)}</td>
                      </tr>
                      <tr>
                        <td>Modelo:</td>
                        <td>{formatValue(device.hardware_details.cpu_info.model)}</td>
                      </tr>
                      <tr>
                        <td>Núcleos Físicos:</td>
                        <td>{formatValue(device.hardware_details.cpu_info.cores)}</td>
                      </tr>
                      <tr>
                        <td>Threads:</td>
                        <td>{formatValue(device.hardware_details.cpu_info.threads)}</td>
                      </tr>
                      <tr>
                        <td>Frequência:</td>
                        <td>{device.hardware_details.cpu_info.frequency_mhz ? `${device.hardware_details.cpu_info.frequency_mhz} MHz` : 'N/A'}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}

              {/* RAM Information */}
              {hasData(device.hardware_details.ram_info) && (
                <div className="detail-section">
                  <h3>Memória RAM</h3>
                  <table>
                    <tbody>
                      <tr>
                        <td>Total:</td>
                        <td>{device.hardware_details.ram_info.total_gb ? `${device.hardware_details.ram_info.total_gb} GB` : 'N/A'}</td>
                      </tr>
                      {device.hardware_details.ram_info.slots_total && (
                        <tr>
                          <td>Slots Totais:</td>
                          <td>{formatValue(device.hardware_details.ram_info.slots_total)}</td>
                        </tr>
                      )}
                      {device.hardware_details.ram_info.slots_used && (
                        <tr>
                          <td>Slots Utilizados:</td>
                          <td>{formatValue(device.hardware_details.ram_info.slots_used)}</td>
                        </tr>
                      )}
                    </tbody>
                  </table>

                  {/* RAM Modules */}
                  {device.hardware_details.ram_info.modules && device.hardware_details.ram_info.modules.length > 0 && (
                    <div className="sub-section">
                      <h4>Módulos de Memória</h4>
                      <table>
                        <thead>
                          <tr>
                            <th>Capacidade</th>
                            <th>Tipo</th>
                            <th>Velocidade</th>
                            <th>Fabricante</th>
                          </tr>
                        </thead>
                        <tbody>
                          {device.hardware_details.ram_info.modules.map((module, index) => (
                            <tr key={index}>
                              <td>{module.capacity_gb ? `${module.capacity_gb} GB` : 'N/A'}</td>
                              <td>{formatValue(module.type)}</td>
                              <td>{module.speed_mhz ? `${module.speed_mhz} MHz` : 'N/A'}</td>
                              <td>{formatValue(module.manufacturer)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}

              {/* Disk Information */}
              {device.hardware_details.disk_info && device.hardware_details.disk_info.length > 0 && (
                <div className="detail-section">
                  <h3>Discos</h3>
                  {device.hardware_details.disk_info.map((disk, index) => (
                    <div key={index} className="sub-section">
                      <h4>{disk.name || `Disco ${index + 1}`}</h4>
                      <table>
                        <tbody>
                          <tr>
                            <td>Modelo:</td>
                            <td>{formatValue(disk.model)}</td>
                          </tr>
                          <tr>
                            <td>Tipo:</td>
                            <td>{formatValue(disk.type)}</td>
                          </tr>
                          <tr>
                            <td>Capacidade Total:</td>
                            <td>{disk.total_gb ? `${disk.total_gb} GB` : 'N/A'}</td>
                          </tr>
                          <tr>
                            <td>Número de Série:</td>
                            <td>{formatValue(disk.serial_number)}</td>
                          </tr>
                        </tbody>
                      </table>

                      {/* Partitions */}
                      {disk.partitions && disk.partitions.length > 0 && (
                        <div className="sub-section">
                          <h5>Partições</h5>
                          <table>
                            <thead>
                              <tr>
                                <th>Letra/Ponto</th>
                                <th>Capacidade</th>
                                <th>Espaço Livre</th>
                                <th>Sistema de Arquivos</th>
                              </tr>
                            </thead>
                            <tbody>
                              {disk.partitions.map((partition, partIndex) => (
                                <tr key={partIndex}>
                                  <td>{formatValue(partition.drive_letter || partition.mountpoint)}</td>
                                  <td>{partition.total_gb ? `${partition.total_gb} GB` : 'N/A'}</td>
                                  <td>{partition.free_gb ? `${partition.free_gb} GB` : 'N/A'}</td>
                                  <td>{formatValue(partition.fstype)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* GPU Information */}
              {hasData(device.hardware_details.gpu_info) && (
                <div className="detail-section">
                  <h3>Placa de Vídeo (GPU)</h3>
                  <table>
                    <tbody>
                      <tr>
                        <td>Fabricante:</td>
                        <td>{formatValue(device.hardware_details.gpu_info.brand)}</td>
                      </tr>
                      <tr>
                        <td>Modelo:</td>
                        <td>{formatValue(device.hardware_details.gpu_info.model)}</td>
                      </tr>
                      <tr>
                        <td>Memória:</td>
                        <td>{device.hardware_details.gpu_info.vram_mb ? `${device.hardware_details.gpu_info.vram_mb} MB` : 'N/A'}</td>
                      </tr>
                      <tr>
                        <td>Versão do Driver:</td>
                        <td>{formatValue(device.hardware_details.gpu_info.driver_version)}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}

              {/* Motherboard Information */}
              {hasData(device.hardware_details.motherboard_info) && (
                <div className="detail-section">
                  <h3>Placa-Mãe</h3>
                  <table>
                    <tbody>
                      <tr>
                        <td>Fabricante:</td>
                        <td>{formatValue(device.hardware_details.motherboard_info.manufacturer)}</td>
                      </tr>
                      <tr>
                        <td>Modelo:</td>
                        <td>{formatValue(device.hardware_details.motherboard_info.model)}</td>
                      </tr>
                      <tr>
                        <td>Número de Série:</td>
                        <td>{formatValue(device.hardware_details.motherboard_info.serial_number)}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}

              {/* Network Information */}
              {device.hardware_details.network_info && device.hardware_details.network_info.length > 0 && (
                <div className="detail-section">
                  <h3>Interfaces de Rede</h3>
                  <table>
                    <thead>
                      <tr>
                        <th>Nome</th>
                        <th>Tipo</th>
                        <th>Endereço MAC</th>
                        <th>Endereços IP</th>
                      </tr>
                    </thead>
                    <tbody>
                      {device.hardware_details.network_info.map((interface_info, index) => (
                        <tr key={index}>
                          <td>{formatValue(interface_info.name)}</td>
                          <td>{formatValue(interface_info.type)}</td>
                          <td>{formatValue(interface_info.mac)}</td>
                          <td>
                            {interface_info.ip_addresses ? 
                              (Array.isArray(interface_info.ip_addresses) ? 
                                interface_info.ip_addresses.join(', ') : 
                                interface_info.ip_addresses) : 
                              'N/A'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Temperature Information */}
              {hasData(device.hardware_details.temperature_info) && (
                <div className="detail-section">
                  <h3>Temperaturas</h3>
                  <table>
                    <thead>
                      <tr>
                        <th>Componente</th>
                        <th>Temperatura</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(device.hardware_details.temperature_info).map(([component, temp], index) => (
                        <tr key={index}>
                          <td>{component}</td>
                          <td>{typeof temp === 'number' ? `${temp}°C` : formatValue(temp)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Power Supply Information */}
              {hasData(device.hardware_details.power_supply_info) && (
                <div className="detail-section">
                  <h3>Fonte de Alimentação</h3>
                  <table>
                    <tbody>
                      <tr>
                        <td>Fabricante:</td>
                        <td>{formatValue(device.hardware_details.power_supply_info.manufacturer)}</td>
                      </tr>
                      <tr>
                        <td>Modelo:</td>
                        <td>{formatValue(device.hardware_details.power_supply_info.model)}</td>
                      </tr>
                      <tr>
                        <td>Potência:</td>
                        <td>{device.hardware_details.power_supply_info.wattage ? `${device.hardware_details.power_supply_info.wattage} W` : 'N/A'}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}

              {/* Custom Notes */}
              {device.hardware_details.custom_notes && (
                <div className="detail-section">
                  <h3>Observações</h3>
                  <p>{device.hardware_details.custom_notes}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="no-hardware-details">
              <p>Nenhum detalhe de hardware disponível para este dispositivo.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DeviceDetail;
