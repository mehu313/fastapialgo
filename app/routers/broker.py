from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import BrokerCredential
from app.models.broker import BracketOrderRequest, BrokerCreate
from app.security.security import encrypt_data
from app.security.auth import get_current_user
from app.services.broker_service import get_user_broker_instance
from app.models.user import User
from app.brokers.delta_india import DeltaBroker

router = APIRouter(prefix="/broker", tags=["Broker"])


@router.post("/add")
def add_or_update_broker(
    broker_data: BrokerCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    encrypted_key = encrypt_data(broker_data.api_key)
    encrypted_secret = encrypt_data(broker_data.api_secret)

    broker = db.query(BrokerCredential).filter(
        BrokerCredential.user_id == current_user.id,
        BrokerCredential.broker_name == broker_data.broker_name
    ).first()

    if broker:
        broker.api_key = encrypted_key
        broker.api_secret = encrypted_secret
        broker.is_active = True
    else:
        broker = BrokerCredential(
            user_id=current_user.id,
            broker_name=broker_data.broker_name,
            api_key=encrypted_key,
            api_secret=encrypted_secret,
        )
        db.add(broker)

    db.commit()
    return {"message": "Broker saved successfully"}


@router.get("/status")
def broker_status(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    broker = db.query(BrokerCredential).filter(
        BrokerCredential.user_id == current_user.id
    ).first()

    if broker:
        return {"connected": True}

    return {"connected": False}

@router.get("/account")
def get_account_data(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    broker = get_user_broker_instance(db, current_user.id)

    return {
        "balance": broker.get_balance(),
        "positions": broker.get_positions(),
    }


@router.post("/order")
def place_order(
    symbol: str,
    side: str,
    quantity: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    broker = get_user_broker_instance(db, current_user.id)

    return broker.place_order(symbol, side, quantity)

from fastapi import APIRouter, Depends, HTTPException
# ... other imports

from app.brokers.delta_india import DeltaBroker # Import your Delta class

@router.get("/orders")
def get_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    broker = get_user_broker_instance(db, current_user.id)
    return broker.get_open_orders()






@router.get("/stop-orders")
def get_stop_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    broker = get_user_broker_instance(db, current_user.id)
    return broker.get_stop_orders()

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session



@router.post("/squareoff")
def square_off_route(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    broker = get_user_broker_instance(db, current_user.id)
    try:
        # Call the existing method
        result = broker.square_off()
        if result.get("success"):
            return {"status": "success", "details": result["details"]}
        else:
            return {"status": "error", "error": result.get("error"), "details": result.get("details")}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/cancel-all-orders")
def cancel_all_orders_route(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    broker = get_user_broker_instance(db, current_user.id)
    result = broker.cancel_all_orders()
    
    if result.get("success"):
        return {"status": "success", "details": result.get("details")}
    
    # This sends the actual error string back to your React app
    return {"status": "error", "error": result.get("error")}




@router.post("/place-bracket-order")
def bracket_order_route(data: dict, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    broker = get_user_broker_instance(db, current_user.id)
    # Extract data: symbol, side, size, sl, target, etc.
    result = broker.place_bracket_order(
        symbol=data.get("symbol"),
        side=data.get("side"),
        size=data.get("size"),
        order_type="market_order",
        stop_loss=data.get("sl"),
        target=data.get("target")
    )
    return result

@router.post("/place-stop-loss")
def place_stop_loss_route(
    data: dict, 
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    """
    Triggers a Market Stop-Loss order for Delta India.
    Expected data: {"product_id": 27, "size": 10, "stop_price": 45000, "side": "sell"}
    """
    broker = get_user_broker_instance(db, current_user.id)
    
    # Extract params from frontend request
    product_id = data.get("product_id")
    size = data.get("size")
    stop_price = data.get("stop_price")
    side = data.get("side") # This should be the 'closing' side

    if not all([product_id, size, stop_price, side]):
        raise HTTPException(status_code=400, detail="Missing required stop-loss parameters")

    try:
        order_id, trigger_price = broker.place_stop_loss_order(
            product_id=int(product_id),
            size=float(size),
            stop_price=float(stop_price),
            sl_side=side.lower()
        )

        if order_id:
            return {
                "status": "success", 
                "order_id": order_id, 
                "trigger_price": trigger_price
            }
        
        return {"status": "error", "message": "Failed to place stop-loss"}

    except Exception as e:
        print(f"Route Error: {str(e)}")
        return {"status": "error", "error": str(e)}