from typing import Any
from decimal import Decimal


class QueryBuilder:
    def __init__(self):
        self.query = {}

    def add_amount(self, value: Decimal, currency: str):
        self.query["amount"] = {"value": str(value), "currency": currency}
        return self
    
    def add_redirect_confirmation(self, redirect_url: str):
        self.query["confirmation"] = {"type": "redirect", "return_url": redirect_url}
        return self
    
    def add_payment_defaults(self):
        self.query["capture"] = True
        self.query["save_payment_method"] = True
        return self
    
    def add_description(self, desc: str):
        self.query["description"] = desc
        return self
    
    def add_payment_id(self, payment_id: str):
        self.query["payment_id"] = payment_id
        return self

    def add_custom_param(self, key: str, value: Any):
        self.query[key] = value
        return self
    
    def add_payment_method(self, method_id: str):
        self.query["payment_method_id"] = method_id
        return self
    
    def add_capture(self, capture: bool):
        self.query["capture"] = capture
        return self
    
    def add_type(self, method_type: str):
        self.query["type"] = method_type
        return self
    
    def build(self) -> dict[str, Any]:
        return self.query
