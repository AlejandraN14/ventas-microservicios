import logging
import os
from typing import Optional, Dict, Any
import mercadopago
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN", "")
MP_API_BASE_URL = "https://api.mercadopago.com/v1"


class MercadoPagoService:
    def __init__(self):
        if not MP_ACCESS_TOKEN:
            raise ValueError("MP_ACCESS_TOKEN no está configurado")
        self.sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

    def create_customer(self, email: str, first_name: str = "", last_name: str = "") -> Optional[Dict[str, Any]]:
        try:
            customer_data = {
                "email": email,
            }
            if first_name:
                customer_data["first_name"] = first_name
            if last_name:
                customer_data["last_name"] = last_name

            logger.info(f"[MP] 📌 Creando customer email={email}")
            response = self.sdk.customer().create(customer_data)
            logger.debug(f"[MP] Response status: {response.get('status')}")
            
            if response.get("status") in (200, 201):
                customer = response.get("response", {})
                logger.info(f"[MP] ✅ Customer creado id={customer.get('id')}")
                return customer
            elif response.get("status") == 400:
                # Verificar si el error es que el cliente ya existe
                cause = response.get("response", {}).get("cause", [])
                if cause and any(c.get("code") == "101" for c in cause):
                    logger.info(f"[MP] ⚠️  Customer ya existe para email={email}, recuperando...")
                    # Intentar obtener el customer por email usando search_customer
                    customer = self.search_customer_by_email(email)
                    if customer:
                        logger.info(f"[MP] ✅ Customer recuperado id={customer.get('id')}")
                        return customer
                logger.error(f"[MP] ❌ Error creando customer: {response}")
                return None
            else:
                logger.error(f"[MP] ❌ Error creando customer status={response.get('status')}: {response}")
                return None
        except Exception as e:
            logger.error(f"[MP] ❌ Excepción creando customer: {e}", exc_info=True)
            return None

    def search_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Busca un customer en Mercado Pago por email"""
        try:
            logger.info(f"[MP] 📌 Buscando customer por email={email}")
            response = self.sdk.customer().search({
                "email": email
            })
            logger.debug(f"[MP] Search response status: {response.get('status')}")
            
            if response.get("status") == 200:
                results = response.get("response", {}).get("results", [])
                if results:
                    customer = results[0]
                    logger.info(f"[MP] ✅ Customer encontrado id={customer.get('id')}")
                    return customer
                else:
                    logger.warning(f"[MP] ⚠️  No se encontró customer con email={email}")
                    return None
            else:
                logger.error(f"[MP] ❌ Error buscando customer por email status={response.get('status')}: {response}")
                return None
        except Exception as e:
            logger.error(f"[MP] ❌ Excepción buscando customer por email: {e}", exc_info=True)
            return None

    def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"[MP] Obteniendo customer id={customer_id}")
            response = self.sdk.customer().get(customer_id)
            
            if response.get("status") == 200:
                return response.get("response", {})
            else:
                logger.error(f"[MP] Error obteniendo customer: {response}")
                return None
        except Exception as e:
            logger.error(f"[MP] Excepción obteniendo customer: {e}")
            return None

    def save_card(self, customer_id: str, token: str) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"[MP] 📌 Guardando tarjeta para customer_id={customer_id}")
            logger.debug(f"[MP] Token: {token[:20]}... (longitud={len(token)})")
            
            # Usar API REST directamente en lugar del SDK
            url = f"{MP_API_BASE_URL}/customers/{customer_id}/cards"
            headers = {
                "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }
            payload = {"token": token}
            
            logger.debug(f"[MP] URL: {url}")
            response = requests.post(url, json=payload, headers=headers)
            status_code = response.status_code
            
            logger.info(f"[MP] Response save_card status: {status_code}")
            
            if status_code in (200, 201):
                card = response.json()
                logger.info(f"[MP] ✅ Tarjeta guardada id={card.get('id')}")
                logger.debug(f"[MP] Response completa: {card}")
                return card
            elif status_code == 400:
                error_data = response.json()
                error_message = error_data.get("message", "")
                cause = error_data.get("cause", [])
                
                logger.warning(f"[MP] ⚠️  Error 400 guardando tarjeta: {error_message}")
                logger.debug(f"[MP] Cause: {cause}")
                
                if "already exists" in error_message.lower() or (cause and any("already exist" in str(c.get("description", "")).lower() for c in cause)):
                    logger.warning(f"[MP] ⚠️  Tarjeta ya existe para customer_id={customer_id}")
                    # Si la tarjeta ya existe, intentar obtener la lista de tarjetas
                    list_url = f"{MP_API_BASE_URL}/customers/{customer_id}/cards"
                    list_response = requests.get(list_url, headers=headers)
                    if list_response.status_code == 200:
                        cards = list_response.json()
                        if cards and len(cards) > 0:
                            logger.info(f"[MP] ✅ Tarjeta existente recuperada id={cards[0].get('id')}")
                            return cards[0]
                
                logger.error(f"[MP] ❌ Error guardando tarjeta: {error_data}")
                return None
            else:
                error_data = response.json() if response.text else {}
                logger.error(f"[MP] ❌ Error guardando tarjeta status={status_code}: {error_data}")
                return None
        except Exception as e:
            logger.error(f"[MP] ❌ Excepción guardando tarjeta: {e}", exc_info=True)
            return None

    def get_card(self, customer_id: str, card_id: str) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"[MP] Obteniendo tarjeta customer_id={customer_id} card_id={card_id}")
            response = self.sdk.card().get(customer_id, card_id)
            
            if response.get("status") == 200:
                return response.get("response", {})
            else:
                logger.error(f"[MP] Error obteniendo tarjeta: {response}")
                return None
        except Exception as e:
            logger.error(f"[MP] Excepción obteniendo tarjeta: {e}")
            return None

    def delete_card(self, customer_id: str, card_id: str) -> bool:
        try:
            logger.info(f"[MP] Eliminando tarjeta customer_id={customer_id} card_id={card_id}")
            response = self.sdk.card().delete(customer_id, card_id)
            
            if response.get("status") in (200, 204):
                logger.info(f"[MP] Tarjeta eliminada")
                return True
            else:
                logger.error(f"[MP] Error eliminando tarjeta: {response}")
                return False
        except Exception as e:
            logger.error(f"[MP] Excepción eliminando tarjeta: {e}")
            return False

    def create_payment_with_saved_card(
        self,
        customer_id: str,
        card_id: str,
        payment_method_id: str,
        transaction_amount: float,
        description: str,
        email: str,
        external_reference: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            payment_data = {
                "transaction_amount": transaction_amount,
                "description": description,
                "payment_method_id": payment_method_id,
                "payer": {
                    "id": customer_id,
                    "email": email,
                },
                "token": card_id,
                "external_reference": external_reference,
                "installments": 1,
                "capture": True,
            }

            logger.info(f"[MP] Creando pago con tarjeta guardada customer_id={customer_id} card_id={card_id} monto={transaction_amount}")
            response = self.sdk.payment().create(payment_data)
            
            if response.get("status") in (200, 201):
                payment = response.get("response", {})
                logger.info(f"[MP] Pago creado id={payment.get('id')} status={payment.get('status')}")
                return payment
            else:
                logger.error(f"[MP] Error creando pago: {response}")
                return None
        except Exception as e:
            logger.error(f"[MP] Excepción creando pago: {e}")
            return None

    def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"[MP] Obteniendo pago id={payment_id}")
            response = self.sdk.payment().get(payment_id)
            
            if response.get("status") == 200:
                return response.get("response", {})
            else:
                logger.error(f"[MP] Error obteniendo pago: {response}")
                return None
        except Exception as e:
            logger.error(f"[MP] Excepción obteniendo pago: {e}")
            return None
