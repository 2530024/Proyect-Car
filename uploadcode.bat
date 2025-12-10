esptool.exe --chip esp32 --port COM7 erase_flash
esptool.exe --chip esp32 --port COM7 write_flash -z 0x1000 micropython_camera_feeeb5ea3_esp32_idf4_4.bin
micropython_camera_feeeb5ea3_esp32_idf4_4.bin
ampy --port COM7 put src/main.py