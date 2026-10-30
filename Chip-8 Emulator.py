import random
import pygame
pygame.init()
screen = pygame.display.set_mode((640, 320))
clock = pygame.time.Clock()
waitkey = -1
memory = [0]* 4096
V = [0] * 16
I = 0
pc = 0x200
stack = []
display = [0] * 2048
delaytimer = 0
soundtimer = 0
drawn = False
font = [
    0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
    0x20, 0x60, 0x20, 0x20, 0x70,  # 1
    0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
    0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
    0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
    0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
    0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
    0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
    0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
    0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
    0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
    0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
    0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
    0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
    0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
    0xF0, 0x80, 0xF0, 0x80, 0x80,  # F
]
keymap = [pygame.K_x, pygame.K_1, pygame.K_2, pygame.K_3,
          pygame.K_q, pygame.K_w, pygame.K_e, pygame.K_a,
          pygame.K_s, pygame.K_d, pygame.K_z, pygame.K_c,
          pygame.K_4, pygame.K_r, pygame.K_f, pygame.K_v]

keys = [False] * 16
for i in range(len(font)):
    memory[0x050 + i] = font[i]
def load_ROM(filelocation):
    with open(filelocation, "rb") as f:
        data = f.read()
    
    for j in range(len(data)):
        memory[0x200 + j] = data[j]
def fetch():
    global pc
    high = memory[pc]
    low = memory[pc + 1]
    opcode = (high << 8) | low
    
    pc += 2
    return opcode
def execute(opcode):
    global display,pc,V,I,delaytimer,soundtimer,waitkey,drawn
    first = (opcode & 0xF000) >> 12
    x = (opcode & 0x0F00) >> 8
    y = (opcode & 0x00F0) >> 4
    n = (opcode & 0x000F)
    nn = (opcode & 0x00FF)
    nnn = (opcode & 0x0FFF)
    
    if opcode == 0x00E0:
        display = [0] * 2048
    elif opcode == 0x00EE:
        pc = stack.pop()
    elif first == 0x1:
        pc = nnn
    elif first == 0x2:
        stack.append(pc)
        pc = nnn
    elif first == 0x3:
        if V[x] == nn:
            pc +=2
    elif first == 0x4:
        if V[x] != nn:
            pc +=2
    elif first == 0x5:
        if V[x] == V[y]:
            pc +=2
    elif first == 0x6:
        V[x] = nn
    elif first == 0x7:
        V[x] = (V[x] + nn) & 0xFF
    elif first == 0x8:
        if n == 0:
            V[x] = V[y]
        elif n == 1:
            V[x] = V[x] | V[y]
            V[0xF] = 0
        elif n == 2:
            V[x] = V[x] & V[y]
            V[0xF] = 0
        elif n == 3:
            V[x] ^= V[y]
            V[0xF] = 0
        elif n == 4:
            total = V[x] + V[y]
            V[x] = total & 0xFF
            if total > 255:
                V[0xF] = 1
            else:
                V[0xF] = 0
        elif n == 5:
            diff = V[x] - V[y]
            V[x] = diff & 0xFF
            if diff >= 0:
                V[0xF] = 1
            else:
                V[0xF] = 0
        elif n == 6:
            rightmostbit = V[y] & 1
            V[x] = V[y] >> 1
            V[0xF] = rightmostbit
            
        elif n == 7:
            diff = V[y] - V[x]
            V[x] = diff & 0xFF
            if diff >= 0:
                V[0xF] = 1
            else:
                V[0xF] = 0
        elif n == 14:
            leftmostbit = V[y] >> 7 & 1
            V[x] = V[y] << 1 & 0xFF
            V[0xF] = leftmostbit
        
        else:
            print(f"Unknown 8 opcode {opcode:04X}")
                
    elif first == 0x9:
        if V[x] != V[y]:
            pc +=2
    elif first == 0xA:
        I = nnn
    elif first == 0xB:
        pc = nnn + V[0]
    elif first == 0xC:
        V[x] = random.randint(0,255) & nn
    
    elif first == 0xD:
        px = V[x] % 64
        py = V[y] % 32
        
        if not drawn:
            V[0xF] = 0
            for row in range(n):
                if py + row >= 32:
                    break
                sprite_byte = memory[I + row]
                for bit in range(8):
                    if px + bit >= 64:
                        break
                    pixel = (sprite_byte >> 7 - bit) & 1
                    if pixel == 1:
                        index = (py + row) * 64 + (px + bit)
                        if display[index] == 1:
                            V[0xF] = 1
                        display[index] ^= 1
            drawn = True
        elif drawn:
            pc -= 2
    elif first == 0xE:
        if nn == 0x9E:
            if keys[V[x]&0xF]:
                pc +=2
        elif nn == 0xA1:
            if not keys[V[x]&0xF]:
                pc += 2
        else:
            print(f"Unknown E opcode {opcode:04X}")
    elif first == 0xF:
        if nn == 0x07:
            V[x] = delaytimer
        elif nn == 0x15:
            delaytimer = V[x]
        elif nn == 0x18:
            soundtimer = V[x]
        elif nn == 0x1E:
            I = I + V[x]
        elif nn == 0x29:
            I = 0x050 + (V[x] & 0xF) * 5 
        elif nn == 0x33:
            digit1 = V[x]//100
            digit2 = (V[x]//10)%10
            digit3 =V[x] % 10
            memory[I] = digit1
            memory[I + 1] = digit2
            memory[I + 2] = digit3
        elif nn == 0x55:
            for l in range(x + 1):
                memory[I + l] = V[l]
            I += x + 1
        elif nn == 0x65:
            for i in range(x + 1):
                V[i] = memory[I + i]
            I += x + 1
        elif nn == 0x0A:
            
            if waitkey == -1:
                for i in range(16):
                    if keys[i]:
                        waitkey = i
                pc -= 2
            else:
                if keys[waitkey]:
                    pc -= 2
                else:
                    V[x] = waitkey
                    waitkey = -1
        
            
            
                
        else:
            print(f"Unknown F opcode {opcode:04X}")
                    
            
    else:
        print(f"Unknown Opcode {opcode:04X}")
    
def draw_screen():
    screen.fill((0, 0, 0))
    for row in range(32):
        for column in range(64):
            if display[row * 64 + column] == 1:
                pygame.draw.rect(screen, (255, 255, 255), (column * 10, row * 10, 10, 10))

##load_ROM("2-ibm-logo.ch8")
##load_ROM("3-corax+.ch8")
##load_ROM("4-flags.ch8")
##load_ROM("6-keypad.ch8")
##load_ROM("5-quirks.ch8")                
##load_ROM("ultimatetictactoe.ch8")
##load_ROM("Pong.ch8")
##load_ROM("Space Invaders [David Winter].ch8")
load_ROM("br8kout.ch8")
#load_ROM("spockpaperscissors.ch8")
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    drawn = False
    for _ in range(10):
        execute(fetch())
    if delaytimer > 0:
        delaytimer -= 1
    if soundtimer > 0:
        soundtimer -= 1
    pressed = pygame.key.get_pressed()
    for i in range(16):
        keys[i] = pressed[keymap[i]]
    
        
   
    draw_screen()
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
        