import psutil

gws = psutil.net_if_stats()  # estatísticas das interfaces
gateways = psutil.net_if_addrs()  # endereços das interfaces

# Outra forma (mais direta) para pegar gateway default
import netifaces
gateways = netifaces.gateways()
default_gateway = gateways.get('default')
print(default_gateway)
