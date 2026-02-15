import time
import hmac
import hashlib
import requests
import json
from delta_rest_client import OrderType, TimeInForce
from app.brokers.base import BrokerBase
from delta_rest_client import DeltaRestClient
from sqlalchemy import and_
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app.models.models import BrokerCredential


class DeltaBroker(BrokerBase):

    BASE_URL = "https://api.india.delta.exchange"

    #def __init__(self, api_key: str, api_secret: str):
    #    self.api_key = api_key
    #    self.api_secret = api_secret
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.client = DeltaRestClient(
            base_url=self.BASE_URL,
            api_key=self.api_key,
            api_secret=self.api_secret
        )

    def _generate_signature(self, method: str, endpoint: str, body: str = ""):
        timestamp = str(int(time.time()))
        
        # ✅ FIX: Change the order to Method + Timestamp + Endpoint + Body
        message = method + timestamp + endpoint + body

        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        return timestamp, signature

    def _headers(self, method: str, endpoint: str, body: str = ""):
        timestamp, signature = self._generate_signature(method, endpoint, body)

        return {
            "api-key": self.api_key,
            "timestamp": timestamp,
            "signature": signature,
            "Content-Type": "application/json",
        }

    # 🔹 Place Order
    def place_order(self, symbol, side, quantity, order_type="market", price=None):
        endpoint = "/v2/orders"
        url = self.BASE_URL + endpoint

        data = {
            "product_id": symbol,
            "size": quantity,
            "side": side.lower(),
            "order_type": order_type,
        }

        if price:
            data["limit_price"] = price

        body = json.dumps(data)

        response = requests.post(
            url,
            data=body,
            headers=self._headers("POST", endpoint, body)
        )

        return response.json()


    # 🔹 Get Balance
    def get_balance(self):
        endpoint = "/v2/wallet/balances"
        url = "https://api.india.delta.exchange" + endpoint

        try:
            response = requests.get(
                url,
                headers=self._headers("GET", endpoint)
            )
            data = response.json()
            
            if data.get("success") is True and "result" in data:
                # Loop through the list to find the USD asset
                for asset in data["result"]:
                    # In your logs, the 'USD' asset holds the 10k INR balance
                    if asset.get("asset_symbol") == "USD":
                        # We return the 'balance_inr' string specifically
                        return asset.get("balance_inr", "0")

            return "0"
        except Exception as e:
            print(f"Error extracting balance_inr: {e}")
            return "0"
    
    def get_open_orders(self):
        """
        Fetch all active orders (limit, stop-loss, triggered) from Delta.
        """
        endpoint = "/v2/orders"
        query_string = "states=open,pending"
        sig_path = f"{endpoint}?{query_string}"
        url = f"https://api.india.delta.exchange{sig_path}"
        #sig_path = f"{endpoint}"
        #url = f"https://api.india.delta.exchange{sig_path}"
        #response = requests.get(url, headers=self._headers("GET", sig_path))

        try:
            print("GET URL:", url)
            response = requests.get(url, headers=self._headers("GET", sig_path))
            data = response.json()
            print("Raw open orders response:", data)

            if data.get("success"):
                return data.get("result", [])

            return []

        except Exception as e:
            print(f"Error fetching open orders: {e}")
            return []


    # 🔹 Get Stop Orders (Stop Loss / Take Profit)
    def get_stop_orders(self):
        endpoint = "/v2/orders"
        url = "https://api.india.delta.exchange" + endpoint
        params = {"states": "untriggered"} # Stop orders stay untriggered until price hits
        
        try:
            response = requests.get(url, headers=self._headers("GET", endpoint), params=params)
            data = response.json()
            # Filter specifically for stop orders if needed
            return data.get("result", []) if data.get("success") else []
        except Exception:
            return []

    # 🔹 Get Positions (Already fixed, but ensure it uses the India URL)
    def get_positions(self):
        endpoint = "/v2/positions/margined" # This endpoint is better for active trades
        url = "https://api.india.delta.exchange" + endpoint
        try:
            response = requests.get(url, headers=self._headers("GET", endpoint))
            data = response.json()
            return data.get("result", []) if data.get("success") else []
        except Exception:
            return []

    

    def square_off1(self):
        """
        Cancel all open orders (limit/stop) and close all positions.
        Returns detailed results for frontend display.
        """
        
        results = {
            "cancel_orders": [],
            "close_positions": []
        }

        try:
            # -----------------------------
            # 1️⃣ Cancel all orders individually
            # -----------------------------
            open_orders = self.get_open_orders()
            results["cancel_orders"] = []

            for order in open_orders:
                order_id = order["id"]

                # Only cancel orders that are still 'open' or 'pending'
                if order["state"] not in ["open", "pending"]:
                    continue

                endpoint = f"/v2/orders/{order_id}"
                url = f"{self.BASE_URL}{endpoint}"

                res = requests.delete(url, headers=self._headers("DELETE", endpoint))

                # Safe JSON parsing
                try:
                    resp_data = res.json() if res.text else {"message": "No content"}
                except ValueError:
                    resp_data = {"message": "Invalid JSON", "raw_text": res.text}

                results["cancel_orders"].append({
                    "order_id": order_id,
                    "status_code": res.status_code,
                    "response": resp_data
                })

                print(f"DEBUG: Cancel order {order_id} - {res.status_code} - {resp_data}")



            # -----------------------------
            # 2️⃣ Fetch all positions and close them
            # -----------------------------
            positions = self.get_positions()
            for pos in positions:
                size = float(pos.get("size", 0))
                if size == 0:
                    continue

                side = "sell" if size > 0 else "buy"
                product_id = pos.get("product_id")

                order_endpoint = "/v2/orders"
                order_url = f"{self.BASE_URL}{order_endpoint}"
                close_data = {
                    "product_id": product_id,
                    "size": abs(size),
                    "side": side,
                    "order_type": "market_order",
                    "reduce_only": True
                }
                body = json.dumps(close_data)
                res = requests.post(
                    order_url,
                    data=body,
                    headers=self._headers("POST", order_endpoint, body)
                )
                results["close_positions"].append({
                    "product_id": product_id,
                    "status_code": res.status_code,
                    "response": res.json() if res.text else res.text
                })
                print(f"Closed position {product_id}: {res.status_code}")

            return {"success": True, "details": results}

        except Exception as e:
            print(f"Square Off CRASHED: {str(e)}")
            return {"success": False, "error": str(e), "details": results}
        
    def square_off(self):
        """
        Cancel all open orders (limit/stop) using the bulk endpoint 
        and close all positions.
        """
        results = {
            "cancel_orders": [],
            "close_positions": []
        }

        try:
            # -----------------------------
            # 1️⃣ Bulk Cancel All Orders
            # -----------------------------
            endpoint = "/v2/orders/all"
            url = f"{self.BASE_URL}{endpoint}"
            
            # Calling DELETE on /orders/all with no params cancels EVERYTHING
            res = requests.delete(url, headers=self._headers("DELETE", endpoint))
            
            try:
                cancel_resp = res.json() if res.text else {"message": "Success"}
            except ValueError:
                cancel_resp = {"message": "Bulk cancel triggered", "status_code": res.status_code}

            results["cancel_orders"].append(cancel_resp)
            print(f"DEBUG: Bulk Cancel All Orders - {res.status_code}")

            # -----------------------------
            # 2️⃣ Fetch all positions and close them
            # -----------------------------
            positions = self.get_positions()
            for pos in positions:
                size = float(pos.get("size", 0))
                if size == 0:
                    continue

                side = "sell" if size > 0 else "buy"
                product_id = pos.get("product_id")

                order_endpoint = "/v2/orders"
                order_url = f"{self.BASE_URL}{order_endpoint}"
                close_data = {
                    "product_id": product_id,
                    "size": abs(size),
                    "side": side,
                    "order_type": "market_order",
                    "reduce_only": True
                }
                body = json.dumps(close_data)
                res = requests.post(
                    order_url,
                    data=body,
                    headers=self._headers("POST", order_endpoint, body)
                )
                
                results["close_positions"].append({
                    "product_id": product_id,
                    "status_code": res.status_code,
                    "response": res.json() if res.text else res.text
                })
                print(f"Closed position {product_id}: {res.status_code}")

            return {"success": True, "details": results}

        except Exception as e:
            print(f"Square Off CRASHED: {str(e)}")
            return {"success": False, "error": str(e), "details": results}
        

    def cancel_all_orders(self):
        results = []
        try:
            # 1️⃣ Fetch open orders
            endpoint_get = "/v2/orders?states=open,pending"
            res_get = requests.get(
                f"{self.BASE_URL}{endpoint_get}", 
                headers=self._headers("GET", endpoint_get)
            )
            
            data = res_get.json()
            all_orders = data.get("result", [])
            
            if not all_orders:
                return {"success": True, "message": "No orders found", "details": []}

            # 2️⃣ Loop and Cancel
            for order in all_orders:
                order_id = order.get("id")
                product_id = order.get("product_id")
                if not order_id: continue
                
                # Base endpoint for the signature (as required by the mismatch log)
                base_endpoint = "/v2/orders"
                url = f"{self.BASE_URL}{base_endpoint}"
                
                # Use only the base_endpoint for headers/signature
                headers = self._headers("DELETE", base_endpoint)
                
                # Send the DELETE request with the parameters separately
                res_delete = requests.delete(
                    url, 
                    params={"id": order_id, "product_id": product_id},
                    headers=headers
                )
                
                try:
                    del_resp = res_delete.json()
                except:
                    del_resp = {"text": res_delete.text}

                results.append({
                    "order_id": order_id, 
                    "status_code": res_delete.status_code,
                    "response": del_resp
                })
                
                print(f"DEBUG: Cancel {order_id} Result: {res_delete.status_code}")
                print(f"DEBUG: Signature Data used: DELETE + timestamp + {base_endpoint}")

            return {"success": True, "details": results}

        except Exception as e:
            print(f"ERROR: {str(e)}")
            return {"success": False, "error": str(e)}
        
    
    def get_client_for_user(self, user_id: int, db: Session, broker_name="delta"):
        """
        Returns a DeltaRestClient instance for the given user.
        """
        user_broker = db.query(BrokerCredential).filter(
            BrokerCredential.user_id == user_id,
            BrokerCredential.broker_name == broker_name,
            BrokerCredential.is_active == True
        ).first()

        if not user_broker:
            raise Exception("User broker not connected")

        client = DeltaRestClient(
            base_url=self.BASE_URL,
            api_key=user_broker.api_key,
            api_secret=user_broker.api_secret
        )
        return client


    
    
    def get_user_broker(user_id: int, db: Session) -> BrokerCredential:
        broker = db.query(BrokerCredential).filter(
            BrokerCredential.user_id == user_id,
            BrokerCredential.is_active == True
        ).first()
        if not broker:
            raise HTTPException(status_code=404, detail="Broker not connected")
        return broker
    

    def place_stop_loss_order(self, product_id: int, size: float, stop_price: float, sl_side: str):
        stop_order = self.client.place_stop_order(
            product_id=product_id,
            size=size,
            side=sl_side,
            order_type=OrderType.MARKET,
            stop_price=stop_price
        )
        if "id" in stop_order:
            print(f"✅ Stop-Loss Placed at {stop_price} (ID: {stop_order['id']})")
            return stop_order["id"], stop_price
        print("❌ Stop-Loss failed!")
        return None, None


    # app/brokers/delta_india.py

    def place_bracket_order(self, symbol, side, size, order_type, limit_price=None, stop_loss=None, target=None):
        results = {"main_order": None, "sl_order": None, "target_order": None}
        endpoint = "/v2/orders"
        
        try:
            # 1. Place Main Entry Order (Symbol is BTCUSD, etc.)
            main_payload = {
                "product_symbol": symbol,
                "side": side,
                "size": int(size),
                "order_type": "market_order",
            }
            body = json.dumps(main_payload)
            res_main = requests.post(f"{self.BASE_URL}{endpoint}", data=body, headers=self._headers("POST", endpoint, body))
            main_data = res_main.json()
            results["main_order"] = main_data

            if not main_data.get("success"):
                return {"success": False, "error": "Main order failed", "details": results}

            # Get product_id from the successful main order for the SL/TP legs
            product_id = main_data["result"]["product_id"]

            # 2. Place Stop-Loss (THIS IS LIKELY WHERE YOUR ERROR IS)
            if stop_loss:
                sl_side = "sell" if side == "buy" else "buy"
                sl_payload = {
                    "product_id": product_id,
                    "size": int(size),
                    "side": sl_side,
                    "order_type": "stop_market_order", # Must be stop_market_order
                    "stop_price": str(stop_loss),
                    "reduce_only": True # Important for SL
                }
                sl_body = json.dumps(sl_payload)
                res_sl = requests.post(f"{self.BASE_URL}{endpoint}", data=sl_body, headers=self._headers("POST", endpoint, sl_body))
                results["sl_order"] = res_sl.json()

            # 3. Place Target (Limit Order)
            if target:
                tp_side = "sell" if side == "buy" else "buy"
                tp_payload = {
                    "product_id": product_id,
                    "side": tp_side,
                    "size": int(size),
                    "order_type": "limit_order",
                    "limit_price": str(target),
                    "reduce_only": True
                }
                tp_body = json.dumps(tp_payload)
                res_tp = requests.post(f"{self.BASE_URL}{endpoint}", data=tp_body, headers=self._headers("POST", endpoint, tp_body))
                results["target_order"] = res_tp.json()

            return {"success": True, "details": results}

        except Exception as e:
            return {"success": False, "error": str(e)}