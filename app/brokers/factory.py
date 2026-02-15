from app.brokers.delta_india import DeltaBroker


def get_broker(broker_name: str, api_key: str, api_secret: str):
    if broker_name == "delta":
        return DeltaBroker(api_key, api_secret)

    raise ValueError("Unsupported broker")
