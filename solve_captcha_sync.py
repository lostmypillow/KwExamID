from captcha_solver import CaptchaSolver

def solve_captcha_sync(image: bytes):
    # Simulate the blocking CPU-intensive captcha-solving function
    solver = CaptchaSolver(image)
    result = solver.solve_captcha()
    return result
