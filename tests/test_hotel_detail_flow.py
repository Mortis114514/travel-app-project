import os
import pandas as pd
from utils.database import get_hotel_by_id, get_all_hotels


def test_get_all_hotels():
    df = get_all_hotels()
    assert not df.empty


def test_get_hotel_by_id_exists():
    df = get_all_hotels()
    if df.empty:
        pytest.skip("No hotels available")
    hid = df.iloc[0]['Hotel_ID']
    h = get_hotel_by_id(hid)
    assert h is not None
    assert 'HotelName' in h
