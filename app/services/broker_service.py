from sqlalchemy.orm import Session
from app.models.models import BrokerCredential
from app.security.security import decrypt_data
from app.brokers.factory import get_broker


def get_user_broker_instance(db: Session, user_id: int):

    broker_record = db.query(BrokerCredential).filter(
        BrokerCredential.user_id == user_id
    ).first()

    if not broker_record:
        raise Exception("Broker not connected")

    api_key = decrypt_data(broker_record.api_key)
    api_secret = decrypt_data(broker_record.api_secret)

    broker = get_broker(
        broker_record.broker_name,
        api_key,
        api_secret
    )

    return broker
