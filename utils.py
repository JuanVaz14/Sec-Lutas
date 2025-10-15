import re

def limpar_cpf(cpf: str) -> str:
    """Remove pontuação e retorna o CPF como string de 11 dígitos."""
    return re.sub(r'[^0-9]', '', cpf).zfill(11) # Limpa e garante 11 dígitos

def formatar_telefone(tel: str) -> str:
    """Formata um telefone (11 dígitos) para o padrão (DD)DDDDD-DDDD."""
    tel_limpo = re.sub(r'[^0-9]', '', tel)
    if len(tel_limpo) == 11:
        return f"({tel_limpo[:2]}){tel_limpo[2:7]}-{tel_limpo[7:]}"
    return tel # Retorna o original se for inválido

def formatar_cep(cep: str) -> str:
    """Formata o CEP (8 dígitos) para o padrão 00000-000."""
    cep_limpo = re.sub(r'[^0-9]', '', cep)
    if len(cep_limpo) == 8:
        return f"{cep_limpo[:5]}-{cep_limpo[5:]}"
    return cep # Retorna o original se for inválido