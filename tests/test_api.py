from main import Api
from unittest.mock import MagicMock
import nighttime

def test_api_dim_bounds():
    # Create the mocked Api reference structure 
    mock_window = MagicMock()
    # Define a weakref mock lambda as it exists natively in main.py
    api = Api(lambda: mock_window)
    
    # Test setting values through the frontend-js api layer
    api.nt_set_dim(75)
    assert nighttime._dim_level == 75

def test_api_red_bounds():
    mock_window = MagicMock()
    api = Api(lambda: mock_window)
    
    api.nt_set_red(101)
    assert nighttime._red_level == 100

def test_api_disable_all():
    mock_window = MagicMock()
    api = Api(lambda: mock_window)
    
    nighttime.set_dim(50)
    nighttime.set_red(50)
    
    api.nt_disable()
    assert nighttime._dim_level == 0
    assert nighttime._red_level == 0

def test_api_get_state():
    mock_window = MagicMock()
    api = Api(lambda: mock_window)
    
    api.nt_set_dim(10)
    api.nt_set_red(20)
    
    state = api.nt_get_state()
    assert state["dim"] == 10
    assert state["red"] == 20

def test_api_hide_command():
    mock_window = MagicMock()
    api = Api(lambda: mock_window)
    
    api.nt_hide()
    mock_window.hide.assert_called_once()
