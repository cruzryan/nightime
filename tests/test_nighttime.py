import nighttime
import pytest

def test_set_dim_clamping():
    # Should safely clamp values outside boundary domains to 0 and 100
    nighttime.set_dim(150)
    assert nighttime._dim_level == 100

    nighttime.set_dim(-50)
    assert nighttime._dim_level == 0

    nighttime.set_dim(50)
    assert nighttime._dim_level == 50

def test_set_red_clamping():
    nighttime.set_red(200)
    assert nighttime._red_level == 100

    nighttime.set_red(-10)
    assert nighttime._red_level == 0

    nighttime.set_red(35)
    assert nighttime._red_level == 35

def test_get_state():
    # Setup test vectors
    nighttime.set_dim(60)
    nighttime.set_red(40)
    
    state = nighttime.get_state()
    assert state == {"dim": 60, "red": 40}

def test_disable_all():
    nighttime.set_dim(80)
    nighttime.set_red(100)
    
    nighttime.disable_all()
    
    assert nighttime._dim_level == 0
    assert nighttime._red_level == 0
