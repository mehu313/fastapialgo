from abc import ABC, abstractmethod


class BrokerBase(ABC):

    @abstractmethod
    def place_order(
        self,
        symbol: str,
        side: str,   # buy / sell
        quantity: int,
        order_type: str = "market",
        price: float | None = None
    ):
        pass

    @abstractmethod
    def square_off(self, symbol: str):
        pass

    @abstractmethod
    def get_positions(self):
        pass
