
'''import random
ans = random.randint(0,30)
while True:
    guess = int(input("Please input your guess integer (0, 30):"))
    if (guess < ans):
        print("Too low")
    elif (guess > ans):
        print("Too high")
    else:
        print("You are right!")
        print("The end")
        break

'''
#You come up with a number and let the computer guess it
print("Please identify a number between 0 and 100 and keep it in your mind")
low = 0
high = 100
while True:
    guess = (low + high) // 2
    ans = str(input("Is your number: {0} (Y/N)? " .format(guess))).upper()
    if ans[0] == 'Y':
        print("Correct")
        break
    elif ans[0] == 'N':
        feedback = str(input("Higher or lower (H/L)? ")).upper()
        if (feedback[0] == 'H'):
            low = guess
        elif (feedback[0] == 'L'):
            high = guess
        else:
            print("Please enter H or L")
    else:
        print("Please enter Y or N")
