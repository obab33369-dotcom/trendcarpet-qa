import os

# Base Directories
ONEDRIVE_DIR = r"C:\Users\AndronikLindgren\OneDrive - CaMa Gruppen AB\Pictures"
NEW_WHITE_BG_DIR = os.path.join(ONEDRIVE_DIR, "Refoma white background fix")
TOPAZ_DIR = os.path.join(ONEDRIVE_DIR, "TEST TOPAZ")
ORIG_DIR = os.path.join(ONEDRIVE_DIR, "reforma_original_images_by_product")
FTP_UPLOAD_DIR = os.path.join(ONEDRIVE_DIR, "turboflow", "ftp_upload_cropped_full")

BRAND_DICT_PATH = r"c:\Users\AndronikLindgren\.gemini\antigravity\scratch\Projects\REFORMA\reforma-turboflow\brand_sku_dict.json"
GEMINI_ENV_PATH = r"C:\Users\AndronikLindgren\reforma_automation\GEMINI_API_KEY.env"

# Target Canvas size
CANVAS_SIZE = 2000

# Category Sizing Configurations
# Format: (target_w, target_h, floor_pct, is_centered)
CATEGORY_TARGETS = {
    "sofa_2_seat": {"target_w": 0.92, "target_h": 0.42, "floor_pct": 0.10, "is_centered": False},
    "sofa_3_seat": {"target_w": 0.94, "target_h": 0.42, "floor_pct": 0.10, "is_centered": False},
    "armchair": {"target_w": 0.92, "target_h": 0.82, "floor_pct": 0.10, "is_centered": False},
    "barstool": {"target_w": 0.75, "target_h": 0.86, "floor_pct": 0.10, "is_centered": False},
    "stool": {"target_w": 0.65, "target_h": 0.68, "floor_pct": 0.10, "is_centered": False},
    "chair_dining": {"target_w": 0.90, "target_h": 0.82, "floor_pct": 0.10, "is_centered": False},
    "table_large": {"target_w": 0.92, "target_h": 0.52, "floor_pct": 0.10, "is_centered": False},
    "table_small": {"target_w": 0.83, "target_h": 0.65, "floor_pct": 0.10, "is_centered": False},
    "cabinet_large": {"target_w": 0.83, "target_h": 0.92, "floor_pct": 0.10, "is_centered": False},
    "cabinet_small": {"target_w": 0.92, "target_h": 0.63, "floor_pct": 0.10, "is_centered": False},
    "shelf_hanging": {"target_w": 0.81, "target_h": 0.40, "floor_pct": 0.50, "is_centered": True},
    "shelf_floor": {"target_w": 0.86, "target_h": 0.86, "floor_pct": 0.10, "is_centered": False},
    "lamp_floor": {"target_w": 0.63, "target_h": 0.90, "floor_pct": 0.10, "is_centered": False},
    "lamp_table": {"target_w": 0.38, "target_h": 0.44, "floor_pct": 0.50, "is_centered": True},
    "lamp_pendant": {"target_w": 0.70, "target_h": 0.58, "floor_pct": 0.50, "is_centered": True},
    "lamp_wall": {"target_w": 0.58, "target_h": 0.46, "floor_pct": 0.50, "is_centered": True},
    "default": {"target_w": 0.86, "target_h": 0.90, "floor_pct": 0.50, "is_centered": True}
}

# Task queue and broker configurations
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
USE_CELERY = os.environ.get("USE_CELERY", "False").lower() in ("true", "1")
LOCAL_SCRATCH_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scratch", "active_downloads")

