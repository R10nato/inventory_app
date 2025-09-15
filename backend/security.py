"""
Módulo de segurança para validação de tokens e assinaturas.
"""
import hmac
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import HTTPException, status, Request
from jose import JWTError, jwt
from pydantic import ValidationError

from .config import settings

# Chave secreta para assinatura JWT (deve ser armazenada de forma segura em produção)
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Cria um novo token de acesso JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verifica e decodifica um token JWT."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_hmac_signature(payload: Dict[str, Any], received_signature: str, secret_key: str) -> bool:
    """
    Verifica a assinatura HMAC-SHA256 de um payload.
    
    Args:
        payload: Dicionário com os dados a serem verificados
        received_signature: Assinatura recebida no cabeçalho
        secret_key: Chave secreta compartilhada
        
    Returns:
        bool: True se a assinatura for válida, False caso contrário
    """
    # Remove a assinatura do payload se estiver presente
    payload_copy = payload.copy()
    payload_copy.pop('signature', None)
    
    # Ordena as chaves para garantir consistência
    sorted_payload = {k: payload_copy[k] for k in sorted(payload_copy)}
    
    # Converte para string JSON com ordenação de chaves consistente
    payload_str = json.dumps(sorted_payload, sort_keys=True, separators=(',', ':'))
    
    # Calcula a assinatura esperada
    hmac_obj = hmac.new(
        key=secret_key.encode('utf-8'),
        msg=payload_str.encode('utf-8'),
        digestmod=hashlib.sha256
    )
    expected_signature = hmac_obj.hexdigest()
    
    # Compara as assinaturas de forma segura contra timing attacks
    return hmac.compare_digest(expected_signature, received_signature)

def get_agent_secret(agent_id: str) -> Optional[str]:
    """
    Obtém a chave secreta de um agente a partir do banco de dados.
    
    Em produção, isso deve buscar do banco de dados ou de um serviço de gerenciamento de segredos.
    """
    # TODO: Implementar busca no banco de dados
    # Por enquanto, retornamos uma chave fixa para testes
    return "sua_chave_secreta_muito_segura"

def get_current_agent(request: Request) -> Dict[str, Any]:
    """
    Middleware para autenticação baseada em token JWT.
    
    Verifica o token JWT no cabeçalho Authorization e retorna os dados do agente.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise credentials_exception
        
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        agent_id: str = payload.get("sub")
        if agent_id is None:
            raise credentials_exception
        return {"agent_id": agent_id, "permissions": payload.get("permissions", [])}
    except JWTError:
        raise credentials_exception
