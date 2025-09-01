from mydisplay import display, show_multiple_text_errors, show_no_errors

# Show multiple text errors as numeric codes
show_multiple_text_errors(
    ["lidar_fail","lidar_com", "gps_fail", "ip_mesh_com"],
    display,
    delay=1.0
)

#show_no_errors(display)

# Start simulator (blocks)
display.run()
