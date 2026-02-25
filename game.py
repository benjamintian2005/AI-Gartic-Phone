import turtle
import anthropic
import time
import os
import random
import base64
import io
import mss
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

WORDS = [
    "apple", "tree", "house", "car", "cat", "dog", "sun", "moon",
    "star", "flower", "heart", "fish", "bird", "boat", "airplane",
    "ice cream", "pizza", "cake", "umbrella", "glasses", "hat",
    "mountain", "cloud", "rainbow", "butterfly", "snake", "circle"
]

BG_COLOR = "#1a1a2e"
CANVAS_COLOR = "#fafafa"
ACCENT_COLOR = "#e94560"
TEXT_COLOR = "#eaeaea"
SUCCESS_COLOR = "#4ecca3"
ERROR_COLOR = "#e94560"

score = {"correct": 0, "total": 0}

# UI globals — initialized in setup_ui()
screen = None
drawer = None
text_turtle = None
score_turtle = None


def setup_ui():
    global screen, drawer, text_turtle, score_turtle

    screen = turtle.Screen()
    screen.bgcolor(BG_COLOR)
    screen.title("AI Gartic Phone")
    screen.setup(width=1000, height=750)

    # Canvas frame border
    frame = turtle.Turtle()
    frame.hideturtle()
    frame.speed(0)
    frame.penup()
    frame.goto(-350, -220)
    frame.pendown()
    frame.pensize(3)
    frame.color(ACCENT_COLOR)
    for _ in range(2):
        frame.forward(700)
        frame.left(90)
        frame.forward(440)
        frame.left(90)
    frame.penup()

    # Canvas fill
    frame.goto(-348, -218)
    frame.color(CANVAS_COLOR)
    frame.begin_fill()
    for _ in range(2):
        frame.forward(696)
        frame.left(90)
        frame.forward(436)
        frame.left(90)
    frame.end_fill()

    drawer = turtle.Turtle()
    drawer.speed(3)
    drawer.pensize(3)
    drawer.color("black")

    text_turtle = turtle.Turtle()
    text_turtle.hideturtle()
    text_turtle.penup()
    text_turtle.goto(0, 290)

    score_turtle = turtle.Turtle()
    score_turtle.hideturtle()
    score_turtle.penup()
    score_turtle.color(TEXT_COLOR)

    # Static labels
    title = turtle.Turtle()
    title.hideturtle()
    title.penup()
    title.goto(0, 320)
    title.color(ACCENT_COLOR)
    title.write("AI GARTIC PHONE", align="center", font=("Courier", 28, "bold"))

    instructions = turtle.Turtle()
    instructions.hideturtle()
    instructions.penup()
    instructions.goto(0, -280)
    instructions.color(TEXT_COLOR)
    instructions.write("[SPACE] New Round    [C] Clear Canvas",
                       align="center", font=("Courier", 12, "normal"))

    subtitle = turtle.Turtle()
    subtitle.hideturtle()
    subtitle.penup()
    subtitle.goto(0, -310)
    subtitle.color("#666666")
    subtitle.write("Claude Artist draws  |  Claude Guesser guesses",
                   align="center", font=("Courier", 11, "normal"))


def update_score_display():
    score_turtle.clear()
    score_turtle.goto(400, 320)
    pct = (score["correct"] / score["total"] * 100) if score["total"] > 0 else 0
    score_turtle.write(f"Score: {score['correct']}/{score['total']} ({pct:.0f}%)",
                       align="right", font=("Courier", 14, "bold"))


def generate_drawing_code(word):
    """Ask Claude to generate turtle drawing code for the given word."""
    prompt = f"""Generate Python turtle code to draw a '{word}' for a Pictionary game.

Requirements:
- Use only turtle commands (no imports, no screen setup)
- Assume turtle object is called 't'
- Keep it simple and recognizable
- Use basic shapes and colors
- Start with t.penup() and t.goto() to position
- Don't include turtle.done() or screen setup
- Just the drawing commands

Example format:
t.penup()
t.goto(0, -50)
t.pendown()
t.color("red")
t.begin_fill()
t.circle(50)
t.end_fill()

Generate ONLY the turtle code, no explanations."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=20000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text
    if "```python" in response_text:
        return response_text.split("```python")[1].split("```")[0].strip()
    elif "```" in response_text:
        return response_text.split("```")[1].split("```")[0].strip()
    return response_text.strip()


def execute_drawing(code):
    """Execute Claude-generated turtle drawing code using the shared drawer."""
    try:
        exec(code, {'t': drawer, 'turtle': turtle})
        return True
    except Exception as e:
        print(f"Error executing drawing code: {e}")
        return False


def clear_canvas():
    drawer.clear()
    drawer.penup()
    drawer.home()
    drawer.pendown()


def screenshot_to_base64():
    """Capture the turtle window and return a base64-encoded PNG string."""
    canvas = screen.getcanvas()
    root = canvas.winfo_toplevel()
    root.update()

    x = root.winfo_rootx()
    y = root.winfo_rooty()
    width = root.winfo_width()
    height = root.winfo_height()

    # Scale logical → physical pixels for HiDPI/Retina displays
    scale = root.winfo_fpixels('1i') / 72.0
    x = int(x * scale)
    y = int(y * scale)
    width = int(width * scale)
    height = int(height * scale)

    print(f"Capturing window at: x={x}, y={y}, width={width}, height={height} (scale={scale})")

    with mss.mss() as sct:
        screenshot = sct.grab({"top": y, "left": x, "width": width, "height": height})
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

    img.save("debug_capture.png")
    print("Debug image saved to debug_capture.png")

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return base64.standard_b64encode(buf.read()).decode('utf-8')


def guess_drawing():
    """Send the current canvas to Claude and return its guess as a string."""
    img_base64 = screenshot_to_base64()

    prompt = """You are playing Pictionary! Look at this drawing and guess what it represents.

Rules:
- Give your SINGLE BEST GUESS as one or two words
- Common Pictionary words include: objects, animals, food, nature, simple concepts
- Just say the word/phrase, no explanations or hedging
- Be confident in your guess!

What is this drawing of?"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img_base64}},
                {"type": "text", "text": prompt}
            ]
        }]
    )
    return message.content[0].text.strip().lower()


def play_round():
    """Run one full round: pick a word, draw it, then have Claude guess."""
    word = random.choice(WORDS)

    clear_canvas()
    text_turtle.clear()
    text_turtle.goto(0, 290)
    text_turtle.color(TEXT_COLOR)
    text_turtle.write("ARTIST is thinking...", align="center", font=("Courier", 18, "bold"))
    screen.update()

    print(f"\n[ARTIST] Drawing: {word}")
    code = generate_drawing_code(word)
    print("Code generated!")
    print(code)

    clear_canvas()
    text_turtle.clear()
    text_turtle.goto(0, 290)
    text_turtle.color(TEXT_COLOR)
    text_turtle.write("ARTIST is drawing...", align="center", font=("Courier", 18, "bold"))
    screen.update()

    if not execute_drawing(code):
        text_turtle.clear()
        text_turtle.goto(0, 290)
        text_turtle.color(ERROR_COLOR)
        text_turtle.write("Drawing failed. Press SPACE to retry.",
                          align="center", font=("Courier", 14, "normal"))
        return

    drawer.hideturtle()
    time.sleep(1)

    text_turtle.clear()
    text_turtle.goto(0, 290)
    text_turtle.color(TEXT_COLOR)
    text_turtle.write("GUESSER is analyzing...", align="center", font=("Courier", 18, "bold"))
    screen.update()

    print("\n[GUESSER] Analyzing the drawing...")
    try:
        ai_guess = guess_drawing()
        print(f"Guess: {ai_guess}")

        score["total"] += 1
        word_lower = word.lower()
        is_correct = (word_lower in ai_guess or
                      ai_guess in word_lower or
                      word_lower.replace(" ", "") in ai_guess.replace(" ", ""))

        text_turtle.clear()
        text_turtle.goto(0, 290)
        if is_correct:
            score["correct"] += 1
            text_turtle.color(SUCCESS_COLOR)
            text_turtle.write(f'CORRECT! Guessed: "{ai_guess.upper()}"',
                              align="center", font=("Courier", 20, "bold"))
            print(">> CORRECT!")
        else:
            text_turtle.color(ERROR_COLOR)
            text_turtle.write(f'WRONG! Guessed: "{ai_guess.upper()}"',
                              align="center", font=("Courier", 20, "bold"))
            print(f">> Wrong! Answer was: {word}")

        text_turtle.goto(0, 255)
        text_turtle.color(TEXT_COLOR)
        text_turtle.write(f"The word was: {word.upper()}",
                          align="center", font=("Courier", 14, "normal"))
        update_score_display()

    except Exception as e:
        print(f"Error with guesser: {e}")
        text_turtle.clear()
        text_turtle.goto(0, 290)
        text_turtle.color(ERROR_COLOR)
        text_turtle.write(f"Guesser failed! Word was: {word.upper()}",
                          align="center", font=("Courier", 16, "bold"))


def main():
    setup_ui()

    text_turtle.color(TEXT_COLOR)
    text_turtle.write("Press SPACE to begin", align="center", font=("Courier", 20, "bold"))
    update_score_display()

    screen.onkey(play_round, "space")
    screen.onkey(clear_canvas, "c")
    screen.listen()

    turtle.done()


if __name__ == "__main__":
    main()
