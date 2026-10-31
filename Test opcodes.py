"""
Standalone CHIP-8 opcode test harness.

Mirrors the opcode logic used in "Chip-8 Emulator.py", but with no pygame
dependency, so it can be run straight from the terminal / Python shell as
console-only proof that the core opcodes behave correctly.

Run with:
    python test_opcodes.py
"""

def new_state():
    """Fresh CPU state for each test, so tests don't interfere with each other."""
    return {
        "memory": [0] * 4096,
        "V": [0] * 16,
        "I": 0,
        "pc": 0x200,
        "stack": [],
    }


def execute(state, opcode):
    """Same opcode-handling logic as the emulator's execute(), minus display/input/timers."""
    memory = state["memory"]
    V = state["V"]

    first = (opcode & 0xF000) >> 12
    x = (opcode & 0x0F00) >> 8
    y = (opcode & 0x00F0) >> 4
    n = (opcode & 0x000F)
    nn = (opcode & 0x00FF)
    nnn = (opcode & 0x0FFF)

    if first == 0x1:
        state["pc"] = nnn
    elif first == 0x2:
        state["stack"].append(state["pc"])
        state["pc"] = nnn
    elif opcode == 0x00EE:
        state["pc"] = state["stack"].pop()
    elif first == 0x3:
        if V[x] == nn:
            state["pc"] += 2
    elif first == 0x4:
        if V[x] != nn:
            state["pc"] += 2
    elif first == 0x6:
        V[x] = nn
    elif first == 0x7:
        V[x] = (V[x] + nn) & 0xFF
    elif first == 0x8 and n == 4:
        total = V[x] + V[y]
        V[x] = total & 0xFF
        V[0xF] = 1 if total > 255 else 0
    elif first == 0x8 and n == 5:
        diff = V[x] - V[y]
        V[x] = diff & 0xFF
        V[0xF] = 1 if diff >= 0 else 0
    elif first == 0xA:
        state["I"] = nnn
    elif first == 0xF and nn == 0x1E:
        state["I"] = state["I"] + V[x]
    elif first == 0xF and nn == 0x33:
        V_x = V[x]
        memory[state["I"]] = V_x // 100
        memory[state["I"] + 1] = (V_x // 10) % 10
        memory[state["I"] + 2] = V_x % 10
    else:
        raise ValueError(f"Opcode {opcode:04X} not handled by this test harness")


def check(description, condition):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {description}")
    return condition


def main():
    results = []

    # 6XNN - set VX to NN
    s = new_state()
    execute(s, 0x6A3C)  # V[A] = 0x3C
    results.append(check("6XNN sets VX correctly (V[A] = 0x3C)", s["V"][0xA] == 0x3C))

    # 7XNN - add NN to VX (no carry flag involved)
    s = new_state()
    s["V"][3] = 0x10
    execute(s, 0x7305)  # V[3] += 0x05
    results.append(check("7XNN adds to VX correctly (0x10 + 0x05 = 0x15)", s["V"][3] == 0x15))

    # 7XNN - wraps around at 255 with no carry flag set
    s = new_state()
    s["V"][3] = 0xFF
    execute(s, 0x7302)  # V[3] += 2, should wrap to 0x01
    results.append(check("7XNN wraps correctly on overflow (0xFF + 2 = 0x01)", s["V"][3] == 0x01))

    # 8XY4 - add VY to VX, set VF on carry
    s = new_state()
    s["V"][0] = 0xF0
    s["V"][1] = 0x20
    execute(s, 0x8014)  # V[0] += V[1], should carry
    results.append(check("8XY4 sets VF=1 on carry (0xF0 + 0x20 > 255)", s["V"][0xF] == 1))
    results.append(check("8XY4 wraps VX correctly on carry", s["V"][0] == 0x10))

    # 8XY4 - no carry case
    s = new_state()
    s["V"][0] = 0x10
    s["V"][1] = 0x10
    execute(s, 0x8014)
    results.append(check("8XY4 sets VF=0 when no carry", s["V"][0xF] == 0))

    # 8XY5 - subtract VY from VX, set VF if no borrow
    s = new_state()
    s["V"][0] = 0x10
    s["V"][1] = 0x05
    execute(s, 0x8015)
    results.append(check("8XY5 subtracts correctly (0x10 - 0x05 = 0x0B)", s["V"][0] == 0x0B))
    results.append(check("8XY5 sets VF=1 when no borrow", s["V"][0xF] == 1))

    # 8XY5 - borrow case
    s = new_state()
    s["V"][0] = 0x05
    s["V"][1] = 0x10
    execute(s, 0x8015)
    results.append(check("8XY5 sets VF=0 on borrow", s["V"][0xF] == 0))

    # ANNN - set I to NNN
    s = new_state()
    execute(s, 0xA123)
    results.append(check("ANNN sets I correctly (I = 0x123)", s["I"] == 0x123))

    # 3XNN - skip next instruction if VX == NN
    s = new_state()
    s["V"][2] = 0x44
    start_pc = s["pc"]
    execute(s, 0x3244)
    results.append(check("3XNN skips when VX == NN", s["pc"] == start_pc + 2))

    # 3XNN - does NOT skip if VX != NN
    s = new_state()
    s["V"][2] = 0x44
    start_pc = s["pc"]
    execute(s, 0x3245)
    results.append(check("3XNN does not skip when VX != NN", s["pc"] == start_pc))

    # 2NNN / 00EE - subroutine call and return
    s = new_state()
    s["pc"] = 0x200
    execute(s, 0x2300)  # call subroutine at 0x300
    call_ok = check("2NNN jumps to NNN and pushes return address", s["pc"] == 0x300 and s["stack"] == [0x200])
    execute(s, 0x00EE)  # return
    return_ok = check("00EE returns to the pushed address", s["pc"] == 0x200 and s["stack"] == [])
    results.append(call_ok)
    results.append(return_ok)

    # FX1E - add VX to I
    s = new_state()
    s["I"] = 0x300
    s["V"][5] = 0x10
    execute(s, 0xF51E)
    results.append(check("FX1E adds VX to I correctly (0x300 + 0x10 = 0x310)", s["I"] == 0x310))

    # FX33 - binary-coded decimal of VX
    s = new_state()
    s["I"] = 0x400
    s["V"][0] = 157
    execute(s, 0xF033)
    bcd_ok = (
        s["memory"][0x400] == 1
        and s["memory"][0x401] == 5
        and s["memory"][0x402] == 7
    )
    results.append(check("FX33 stores correct BCD digits for 157 (1, 5, 7)", bcd_ok))

    print()
    passed = sum(results)
    total = len(results)
    print(f"{passed}/{total} opcode tests passed.")
    if passed == total:
        print("All tested opcodes behave correctly.")
    else:
        print("Some opcodes failed — check output above.")


if __name__ == "__main__":
    main()