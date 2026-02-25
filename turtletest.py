import turtle

# Set up screen
screen = turtle.Screen()
screen.bgcolor("lightblue")

# Create turtle
t = turtle.Turtle()
t.speed(3)
t.width(3)

# Draw the cone
t.penup()
t.goto(0, -150)
t.pendown()
t.color("saddlebrown", "peru")
t.begin_fill()
t.goto(-80, 50)
t.goto(80, 50)
t.goto(0, -150)
t.end_fill()

# Draw the ice cream scoop
t.penup()
t.goto(0, 50)
t.pendown()
t.color("pink", "lightpink")
t.begin_fill()
t.circle(60)
t.end_fill()

# Add sprinkles
t.penup()
t.color("red")
for x, y in [(-20, 120), (10, 130), (25, 110), (-30, 100)]:
    t.goto(x, y)
    t.dot(8)

# Finish
t.hideturtle()
screen.mainloop()
