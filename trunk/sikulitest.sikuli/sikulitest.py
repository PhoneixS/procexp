import subprocess

subprocess.Popen(["killall", "python"])


for _ in range(5):
    p = subprocess.Popen(["procexp.sh"])
    
    
    type("1388435202633.png", "test")
    click("1388435311540.png")
    
    click("1388436794512.png")
    
    
    #test CPU affinity
    proc = subprocess.Popen(["python", "-c", "while True:  pass"])
    
    type(Key.SPACE, KEY_ALT)
    type("x")
    
    click(Pattern("1388436205289.png").targetOffset(-33,-3))
    
    doubleClick("1388436274469.png")
    
    doubleClick("1388436357270.png")
    
    rightClick("1388436426300.png")
    
    type(Key.DOWN)
    type(Key.DOWN)
    type(Key.DOWN)
    type(Key.DOWN)
    type(Key.DOWN)
    type(Key.DOWN)
    type(Key.ENTER)
    
    wait("1388437073840.png", 30)
    
    wait("1388437097963.png", 90)
    
    p = subprocess.Popen(["killall", "python"])
