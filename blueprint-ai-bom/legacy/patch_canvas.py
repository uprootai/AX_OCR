#!/usr/bin/env python3
"""
Patch streamlit-drawable-canvas to handle background images properly
"""
import os
import site

# Find the streamlit-drawable-canvas package location
site_packages = site.getsitepackages()
canvas_path = None

for path in site_packages:
    potential_path = os.path.join(path, 'streamlit_drawable_canvas', '__init__.py')
    if os.path.exists(potential_path):
        canvas_path = potential_path
        break

if not canvas_path:
    # Try user site packages
    import streamlit_drawable_canvas
    canvas_path = os.path.join(os.path.dirname(streamlit_drawable_canvas.__file__), '__init__.py')

if canvas_path and os.path.exists(canvas_path):
    print(f"Patching {canvas_path}...")

    with open(canvas_path, 'r') as f:
        content = f.read()

    # Find and replace the problematic image_to_url usage
    old_code = """    # Resize background_image to canvas dimensions by default
    # Then override background_color
    background_image_url = None
    if background_image:
        background_image = _resize_img(background_image, height, width)
        # Reduce network traffic and cache when switch another configure, use streamlit in-mem filemanager to convert image to URL
        background_image_url = st_image.image_to_url(
            background_image, width, True, "RGB", "PNG", f"drawable-canvas-bg-{md5(background_image.tobytes()).hexdigest()}-{key}"
        )
        background_image_url = st._config.get_option("server.baseUrlPath") + background_image_url
        background_color = \"\""""

    new_code = """    # Resize background_image to canvas dimensions by default
    # Then override background_color
    background_image_url = None
    if background_image:
        background_image = _resize_img(background_image, height, width)
        # Convert to base64 data URL
        import base64
        from io import BytesIO
        buffered = BytesIO()
        background_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        background_image_url = f"data:image/png;base64,{img_str}"
        background_color = \"\""""

    if old_code in content:
        content = content.replace(old_code, new_code)
        with open(canvas_path, 'w') as f:
            f.write(content)
        print("Patch applied successfully!")
    else:
        # Remove duplicate _img_to_array calls if they exist
        lines = content.split('\n')
        new_lines = []
        skip_next = False

        for i, line in enumerate(lines):
            # Skip duplicate _img_to_array lines
            if skip_next and "_img_to_array" in line:
                skip_next = False
                print(f"Removed duplicate _img_to_array at line {i+1}")
                continue

            # Check if this is the resize line that needs array conversion
            if "background_image = _resize_img(background_image" in line:
                new_lines.append(line)
                # Check if next line already has _img_to_array
                if i+1 < len(lines) and "_img_to_array" in lines[i+1]:
                    print(f"Array conversion already exists at line {i+2}")
                else:
                    # Add conversion to array after resize
                    new_lines.append("        background_image = _img_to_array(background_image)")
                    print(f"Added array conversion at line {i+2}")
                    skip_next = True
            else:
                new_lines.append(line)

        content = '\n'.join(new_lines)
        with open(canvas_path, 'w') as f:
            f.write(content)
        print("Alternative patch applied!")
else:
    print("streamlit-drawable-canvas package not found!")