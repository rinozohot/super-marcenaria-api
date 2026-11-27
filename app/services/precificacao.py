from decimal import Decimal
from fastapi import HTTPException

def calcular_preco_parametrico(
    preco_base: Decimal,
    medida_min: Decimal,
    medida_max: Decimal,
    largura_escolhida: Decimal,
    adicional_material: Decimal = Decimal("0.00"),
    is_assinante_clube: bool = False
) -> Decimal:
    if not (medida_min <= largura_escolhida <= medida_max):
        raise HTTPException(
            status_code=400,
            detail=f"Medida fora do limite fabril ({medida_min}cm a {medida_max}cm)."
        )

    fator_proporcao = largura_escolhida / medida_min
    preco_calculado = (preco_base * fator_proporcao) + adicional_material

    if is_assinante_clube:
        preco_calculado *= Decimal("0.90")

    return round(preco_calculado, 2)
