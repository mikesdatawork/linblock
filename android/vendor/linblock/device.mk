# device.mk - LinBlock product configuration

$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base.mk)

PRODUCT_NAME := linblock_x86_64
PRODUCT_DEVICE := x86_64
PRODUCT_BRAND := LinBlock
PRODUCT_MODEL := LinBlock Emulator
PRODUCT_MANUFACTURER := LinBlock

# Minimal packages
PRODUCT_PACKAGES += \
    Launcher3QuickStep \
    Settings \
    SystemUI \
    DocumentsUI \
    SettingsProvider \
    Shell \
    Traceur

# No Google services
PRODUCT_PACKAGES_REMOVE += \
    GmsCore \
    GoogleServicesFramework \
    Phonesky

# Properties
PRODUCT_PROPERTY_OVERRIDES += \
    ro.hardware=linblock \
    ro.emulator=true \
    ro.adb.secure=0 \
    persist.sys.usb.config=adb
