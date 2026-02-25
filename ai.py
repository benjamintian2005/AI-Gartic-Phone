import turtle
import anthropic
import time
import os
import base64
import io
import mss
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

WORDS = [
    "apple", "tree", "house", "car", "cat", "dog", "sun", "moon", 
    "star", "flower", "heart", "fish", "bird", "boat", "airplane",
    "ice cream", "pizza", "cake", "umbrella", "glasses", "hat",
    "mountain", "cloud", "rainbow", "butterfly", "snake", "circle"
]

# Colors
BG_COLOR = "#1a1a2e"
CANVAS_COLOR = "#fafafa"
ACCENT_COLOR = "#e94560"
TEXT_COLOR = "#eaeaea"
SUCCESS_COLOR = "#4ecca3"
ERROR_COLOR = "#e94560"

# Score tracking
score = {"correct": 0, "total": 0}

# Set up the screen
screen = turtle.Screen()
screen.bgcolor(BG_COLOR)
screen.title("AI Gartic Phone")
screen.setup(width=1000, height=750)

# Draw canvas frame
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

# Fill canvas area
frame.goto(-348, -218)
frame.color(CANVAS_COLOR)
frame.begin_fill()
for _ in range(2):
    frame.forward(696)
    frame.left(90)
    frame.forward(436)
    frame.left(90)
frame.end_fill()

# Create drawing turtle
drawer = turtle.Turtle()
drawer.speed(3)
drawer.pensize(3)
drawer.color("black")

# Create text turtle for displaying info (status area at top)
text_turtle = turtle.Turtle()
text_turtle.hideturtle()
text_turtle.penup()
text_turtle.goto(0, 290)

# Create score display turtle
score_turtle = turtle.Turtle()
score_turtle.hideturtle()
score_turtle.penup()
score_turtle.color(TEXT_COLOR)

def update_score_display():
    """Update the score display"""
    score_turtle.clear()
    score_turtle.goto(400, 320)
    pct = (score["correct"] / score["total"] * 100) if score["total"] > 0 else 0
    score_turtle.write(f"Score: {score['correct']}/{score['total']} ({pct:.0f}%)", 
                      align="right", 
                      font=("Courier", 14, "bold"))

def get_turtle_code_from_claude(word):
    """Ask Claude to generate turtle drawing code for a word"""
    
    prompt = f"""Generate Python turtle code to draw a  '{word}' for a Pictionary game.

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
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    # Extract code from response
    response_text = message.content[0].text
    
    # Remove markdown code blocks if present
    if "```python" in response_text:
        code = response_text.split("```python")[1].split("```")[0].strip()
    elif "```" in response_text:
        code = response_text.split("```")[1].split("```")[0].strip()
    else:
        code = response_text.strip()
    
    return code

def execute_turtle_code(code):
    """Execute the turtle drawing code"""
    try:
        # Create a namespace with the turtle object
        namespace = {'t': drawer, 'turtle': turtle}
        exec(code, namespace)
        return True
    except Exception as e:
        print(f"Error executing code: {e}")
        return False

def clear_canvas():
    """Clear the drawing"""
    drawer.clear()
    drawer.penup()
    drawer.home()
    drawer.pendown()

def capture_canvas_as_image():
    """Capture the turtle canvas as a base64-encoded image using mss"""
    # Get the turtle canvas window position and size
    canvas = screen.getcanvas()
    root = canvas.winfo_toplevel()
    root.update()
    
    # Get window position and size
    x = root.winfo_rootx()
    y = root.winfo_rooty()
    width = root.winfo_width()
    height = root.winfo_height()
    
    print(f"Capturing window at: x={x}, y={y}, width={width}, height={height}")
    
    # Use mss to capture the screen region
    with mss.mss() as sct:
        monitor = {"top": y, "left": x, "width": width, "height": height}
        screenshot = sct.grab(monitor)
        
        # Convert to PIL Image
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
    
    # Debug: save the image to see what's being captured
    img.save("debug_capture.png")
    print("Debug image saved to debug_capture.png")
    
    # Save to bytes
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    # Encode as base64
    img_base64 = base64.standard_b64encode(img_buffer.read()).decode('utf-8')
    
    return img_base64

def ai_guess_drawing():
    """Have Claude look at the drawing and guess what it is"""
    
    # Capture the current canvas
    img_base64 = capture_canvas_as_image()
    
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
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": img_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    )
    
    return message.content[0].text.strip().lower()

def play_round():
    """Play one round of Pictionary with AI guesser"""
    import random
    
    # Pick random word
    word = random.choice(WORDS)
    
    # Display status
    text_turtle.clear()
    text_turtle.goto(0, 290)
    text_turtle.color(TEXT_COLOR)
    text_turtle.write("ARTIST is thinking...", 
                     align="center", 
                     font=("Courier", 18, "bold"))
    
    screen.update()
    
    # Get drawing code from Claude
    print(f"\n[ARTIST] Drawing: {word}")
    code = get_turtle_code_from_claude(word)
    print("Code generated!")
    print(code)
    
    # Clear and draw
    clear_canvas()
    text_turtle.clear()
    text_turtle.goto(0, 290)
    text_turtle.color(TEXT_COLOR)
    text_turtle.write("ARTIST is drawing...", 
                     align="center", 
                     font=("Courier", 18, "bold"))
    
    screen.update()
    
    # Execute the drawing
    success = execute_turtle_code(code)
    
    if success:
        # Drawing complete - now let AI guess!
        drawer.hideturtle()
        time.sleep(1)
        
        text_turtle.clear()
        text_turtle.goto(0, 290)
        text_turtle.color(TEXT_COLOR)
        text_turtle.write("GUESSER is analyzing...", 
                         align="center", 
                         font=("Courier", 18, "bold"))
        screen.update()
        
        # Get AI guess from the image
        print("\n[GUESSER] Analyzing the drawing...")
        try:
            ai_guess = ai_guess_drawing()
            print(f"Guess: {ai_guess}")
            
            # Update score
            score["total"] += 1
            
            # Check if guess is correct (flexible matching)
            word_lower = word.lower()
            is_correct = (word_lower in ai_guess or 
                         ai_guess in word_lower or
                         word_lower.replace(" ", "") in ai_guess.replace(" ", ""))
            
            # Display result
            text_turtle.clear()
            text_turtle.goto(0, 290)
            
            if is_correct:
                score["correct"] += 1
                text_turtle.color(SUCCESS_COLOR)
                text_turtle.write(f'CORRECT! Guessed: "{ai_guess.upper()}"', 
                                 align="center", 
                                 font=("Courier", 20, "bold"))
                print(">> CORRECT!")
            else:
                text_turtle.color(ERROR_COLOR)
                text_turtle.write(f'WRONG! Guessed: "{ai_guess.upper()}"', 
                                 align="center", 
                                 font=("Courier", 20, "bold"))
                print(f">> Wrong! Answer was: {word}")
            
            # Show actual answer below
            text_turtle.goto(0, 255)
            text_turtle.color(TEXT_COLOR)
            text_turtle.write(f"The word was: {word.upper()}", 
                             align="center", 
                             font=("Courier", 14, "normal"))
            
            # Update score display
            update_score_display()
            
        except Exception as e:
            print(f"Error with AI guesser: {e}")
            text_turtle.clear()
            text_turtle.goto(0, 290)
            text_turtle.color(ERROR_COLOR)
            text_turtle.write(f"Guesser failed! Word was: {word.upper()}", 
                             align="center", 
                             font=("Courier", 16, "bold"))
    else:
        text_turtle.clear()
        text_turtle.goto(0, 290)
        text_turtle.color(ERROR_COLOR)
        text_turtle.write("Drawing failed. Press SPACE to retry.", 
                         align="center", 
                         font=("Courier", 14, "normal"))

def new_round():
    """Start a new round"""
    clear_canvas()
    play_round()

# Bind keyboard
screen.onkey(new_round, "space")
screen.onkey(clear_canvas, "c")
screen.listen()

# Display title
title = turtle.Turtle()
title.hideturtle()
title.penup()
title.goto(0, 320)
title.color(ACCENT_COLOR)
title.write("AI GARTIC PHONE", 
           align="center", 
           font=("Courier", 28, "bold"))

# Display instructions
instructions = turtle.Turtle()
instructions.hideturtle()
instructions.penup()
instructions.goto(0, -280)
instructions.color(TEXT_COLOR)
instructions.write("[SPACE] New Round    [C] Clear Canvas", 
                  align="center", 
                  font=("Courier", 12, "normal"))

# Subtitle
subtitle = turtle.Turtle()
subtitle.hideturtle()
subtitle.penup()
subtitle.goto(0, -310)
subtitle.color("#666666")
subtitle.write("Claude Artist draws  |  Claude Guesser guesses", 
              align="center", 
              font=("Courier", 11, "normal"))

# Start message
text_turtle.color(TEXT_COLOR)
text_turtle.write("Press SPACE to begin", 
                 align="center", 
                 font=("Courier", 20, "bold"))

# Initialize score display
update_score_display()

# Keep window open
turtle.done()