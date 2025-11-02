"""Test login page rendering"""
from pages.login_page import create_login_layout

# Try to create login page
try:
    layout = create_login_layout()
    print("SUCCESS: Login page created")
    print(f"Type: {type(layout)}")
    print(f"Layout has {len(layout.children)} children" if hasattr(layout, 'children') else "Layout structure OK")
except Exception as e:
    print(f"ERROR: Login page creation failed: {e}")
    import traceback
    traceback.print_exc()
