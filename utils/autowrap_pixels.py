def autowrap_pixels(text, max_width=120):
    words = text.split()
    lines = []
    current_line = ""
    
    for word in words:
        test_line = word if not current_line else current_line + " " + word
        if M5.Lcd.textWidth(test_line) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
            
    if current_line:
        lines.append(current_line)
    return lines