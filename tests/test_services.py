import pytest
from app.services.tools import get_order_status, search_product
from app.services.memory import MemoryService


class TestOrderStatus:
    def test_existing_order(self):
        result = get_order_status("ORD001")
        assert "Shipped" in result
        assert "2026-07-02" in result

    def test_case_insensitive(self):
        result = get_order_status("ord001")
        assert "ORD001" in result

    def test_nonexistent_order(self):
        result = get_order_status("ORD999")
        assert "not found" in result


class TestProductSearch:
    def test_exact_match(self):
        result = search_product("Wireless Mouse")
        assert "$25" in result
        assert "In Stock" in result

    def test_partial_word_match(self):
        result = search_product("keyboard")
        assert "Mechanical Keyboard" in result

    def test_no_match(self):
        result = search_product("smartphone")
        assert "No products found" in result

    def test_out_of_stock(self):
        result = search_product("Laptop Stand")
        assert "Out of Stock" in result


class TestMemoryService:
    def test_add_and_get(self):
        svc = MemoryService()
        svc.add_message("s1", "user", "hello")
        history = svc.get_history("s1")
        assert len(history) == 1
        assert history[0] == {"role": "user", "content": "hello"}

    def test_session_isolation(self):
        svc = MemoryService()
        svc.add_message("s1", "user", "msg1")
        svc.add_message("s2", "user", "msg2")
        assert len(svc.get_history("s1")) == 1
        assert len(svc.get_history("s2")) == 1

    def test_auto_trim(self):
        svc = MemoryService()
        for i in range(25):
            svc.add_message("s1", "user", f"msg{i}")
        assert len(svc.get_history("s1")) == 20

    def test_clear(self):
        svc = MemoryService()
        svc.add_message("s1", "user", "hello")
        svc.clear("s1")
        assert len(svc.get_history("s1")) == 0
