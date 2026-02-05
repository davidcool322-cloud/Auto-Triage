import os
import pytest
from unittest.mock import patch, MagicMock
import streamlit as st
from src.shared.bmc_credentials import get_bmc_credentials

class TestBMCCredentials:
    
    def setup_method(self):
        # 每次測試前重置 session_state
        if hasattr(st, "session_state"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]

    @patch.dict(os.environ, {"BMC_DEFAULT_USER": "TEST_USER", "BMC_DEFAULT_PASSWORD": "TEST_PASSWORD"})
    def test_get_credentials_defaults_from_env(self):
        """測試當 session_state 為空時，應從環境變數讀取預設值"""
        ip, user, password = get_bmc_credentials()
        assert user == "TEST_USER"
        assert password == "TEST_PASSWORD"
        assert ip == ""

    def test_get_credentials_from_session(self):
        """測試從 session_state 讀取已設定的值"""
        st.session_state["bmc_ip"] = "192.168.1.100"
        st.session_state["bmc_user"] = "admin"
        st.session_state["bmc_password"] = "secret"
        
        ip, user, password = get_bmc_credentials()
        assert ip == "192.168.1.100"
        assert user == "admin"
        assert password == "secret"

    @patch.dict(os.environ, {}, clear=True)
    def test_get_credentials_no_env(self):
        """測試當無環境變數且無 session 時，應回傳空字串"""
        # 模擬完全沒有這些環境變數
        if "BMC_DEFAULT_USER" in os.environ: del os.environ["BMC_DEFAULT_USER"]
        if "BMC_DEFAULT_PASSWORD" in os.environ: del os.environ["BMC_DEFAULT_PASSWORD"]
        
        ip, user, password = get_bmc_credentials()
        assert user == ""
        assert password == ""
