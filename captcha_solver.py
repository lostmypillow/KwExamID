from transformers import pipeline, logging
import cv2
import numpy as np

from transformers import pipeline
import cv2
import numpy as np
from PIL import Image

class CaptchaSolver:
    def __init__(self, image_bytes):
        self.image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        self.kernel = np.ones((2, 2), np.uint8)
        self.pipe = pipeline("image-to-text", model="microsoft/trocr-large-printed")

    def enhance_legibility(self, cropped_image):
        gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU
        )
        return cv2.erode(cv2.blur(mask, (2, 2)), self.kernel, iterations=1)

    def convert_to_pil(self, image_array):
        """Convert a NumPy array (OpenCV image) to a PIL Image."""
        return Image.fromarray(cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB))

    def math_operation(self, left_number, right_number, operation='+'):
        if left_number.isdigit() and right_number.isdigit():
            return eval(f"{int(left_number)} {operation} {int(right_number)}")
        else:
            return None

    def math_operation_for_both_signs(self, left_number, right_number):
        if left_number.isdigit() and right_number.isdigit():
            return int(left_number) + int(right_number)
        else:
            return None

    def resolve(self, left_image, right_image, sign_image, negative_sign_right_image):
        # Convert OpenCV images to PIL Images
        sign_pil = self.convert_to_pil(sign_image)
        left_pil = self.convert_to_pil(left_image)
        right_pil = self.convert_to_pil(right_image)
        negative_sign_right_pil = self.convert_to_pil(negative_sign_right_image)

        # Process with the pipeline
        sign = self.pipe(sign_pil)[0]['generated_text']
        left_number = self.pipe(left_pil)[0]['generated_text']

        if sign in {'+', '@', '4', '*'}:
            right_number = self.pipe(right_pil)[0]['generated_text']
            return self.math_operation(left_number, right_number)
        elif sign in {'-', '='}:
            right_number = self.pipe(negative_sign_right_pil)[0]['generated_text']
            return self.math_operation(left_number, right_number, '-')
        else:
            unfixed_right_number = ''.join(
                char for char in self.pipe(right_pil)[0]['generated_text'] if char.isdigit()
            )
            return self.math_operation_for_both_signs(left_number, unfixed_right_number)

    def solve_captcha(self):
        # Define positions and dimensions for image slicing
        positions = {'left': 5, 'right': 62, 'sign': 39, 'negative_sign_right': 56}
        dimensions = {
            'width': 27, 'height': 36, 
            'width_sign': 15, 'height_sign': 15, 
            'width_negative_sign': 18
        }

        # Crop sections from the main image
        left_image = self.image[6:36, positions['left']:positions['left']+27]
        right_image = self.image[6:36, positions['right']:positions['right']+24]
        sign_image = self.image[10:25, positions['sign']:positions['sign']+dimensions['width_sign']]
        negative_sign_right_image = self.image[7:27, positions['negative_sign_right']:positions['negative_sign_right']+dimensions['width_negative_sign']]

        # Enhance the cropped images for better legibility
        left_enhanced = self.enhance_legibility(left_image)
        right_enhanced = self.enhance_legibility(right_image)
        negative_sign_right_enhanced = self.enhance_legibility(negative_sign_right_image)

        # Pass the enhanced images directly to the resolve function
        return self.resolve(left_enhanced, right_enhanced, sign_image, negative_sign_right_enhanced)

def captcha_solver(image: bytes):
    # Simulate the blocking CPU-intensive captcha-solving function
    solver = CaptchaSolver(image)
    result = solver.solve_captcha()
    return result


