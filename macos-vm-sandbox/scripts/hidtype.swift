// Full-fidelity keyboard input for a guest: HID-state CGEvents posted at the
// HID tap, so event taps, input methods and keyboard hooks see real key events
// with their Unicode text. Assumes the US (ANSI) layout.
//
// Build on the host (target the guest's macOS, which may be older) and copy in:
//   swiftc -O -target arm64-apple-macos14 hidtype.swift -o /tmp/hidtype
//   sbx scp <vm> /tmp/hidtype :hidtype
// Run as root in the GUI session (no TCC grant needed):
//   sbx ssh <vm> "sudo launchctl asuser \$(id -u lume) ~/hidtype type 'Hello, World'"
//   sbx ssh <vm> "sudo launchctl asuser \$(id -u lume) ~/hidtype key escape"
//   sbx ssh <vm> "sudo launchctl asuser \$(id -u lume) ~/hidtype key a cmd shift"
//
// Modifiers are sent as real modifier key-down/up events. Setting only the
// event flags types the unshifted character and leaks Shift into the next key.

import CoreGraphics
import Foundation

let keycodes: [String: CGKeyCode] = [
  "a": 0, "s": 1, "d": 2, "f": 3, "h": 4, "g": 5, "z": 6, "x": 7, "c": 8, "v": 9,
  "b": 11, "q": 12, "w": 13, "e": 14, "r": 15, "y": 16, "t": 17, "1": 18, "2": 19,
  "3": 20, "4": 21, "6": 22, "5": 23, "=": 24, "9": 25, "7": 26, "-": 27, "8": 28,
  "0": 29, "]": 30, "o": 31, "u": 32, "[": 33, "i": 34, "p": 35, "l": 37, "j": 38,
  "'": 39, "k": 40, ";": 41, "\\": 42, ",": 43, "/": 44, "n": 45, "m": 46, ".": 47,
  "`": 50, " ": 49,
  "return": 36, "tab": 48, "space": 49, "delete": 51, "escape": 53,
  "forwarddelete": 117, "home": 115, "end": 119, "pageup": 116, "pagedown": 121,
  "left": 123, "right": 124, "down": 125, "up": 126,
  "f1": 122, "f2": 120, "f3": 99, "f4": 118, "f5": 96, "f6": 97,
  "f7": 98, "f8": 100, "f9": 101, "f10": 109, "f11": 103, "f12": 111,
]

let shifted: [Character: Character] = [
  "!": "1", "@": "2", "#": "3", "$": "4", "%": "5", "^": "6", "&": "7", "*": "8",
  "(": "9", ")": "0", "_": "-", "+": "=", "{": "[", "}": "]", "|": "\\", ":": ";",
  "\"": "'", "<": ",", ">": ".", "?": "/", "~": "`",
]

let modifiers: [String: (code: CGKeyCode, flag: CGEventFlags)] = [
  "shift": (56, .maskShift), "cmd": (55, .maskCommand),
  "option": (58, .maskAlternate), "alt": (58, .maskAlternate), "ctrl": (59, .maskControl),
]

let source = CGEventSource(stateID: .hidSystemState)
let delay: useconds_t = 15_000

func post(_ code: CGKeyCode, down: Bool, flags: CGEventFlags) {
  let event = CGEvent(keyboardEventSource: source, virtualKey: code, keyDown: down)!
  event.flags = flags
  event.post(tap: .cghidEventTap)
  usleep(delay)
}

func press(_ code: CGKeyCode, mods: [String]) {
  var flags: CGEventFlags = []
  for name in mods {
    let mod = modifiers[name]!
    flags.insert(mod.flag)
    post(mod.code, down: true, flags: flags)
  }
  post(code, down: true, flags: flags)
  post(code, down: false, flags: flags)
  for name in mods.reversed() {
    let mod = modifiers[name]!
    flags.remove(mod.flag)
    post(mod.code, down: false, flags: flags)
  }
}

func fail(_ message: String) -> Never {
  FileHandle.standardError.write("hidtype: \(message)\n".data(using: .utf8)!)
  exit(1)
}

let args = Array(CommandLine.arguments.dropFirst())
switch args.first {
case "type" where args.count == 2:
  for ch in args[1] {
    if ch == "\n" {
      press(keycodes["return"]!, mods: [])
    } else if let code = keycodes[String(ch)] {
      press(code, mods: [])
    } else if ch.isUppercase, let code = keycodes[ch.lowercased()] {
      press(code, mods: ["shift"])
    } else if let base = shifted[ch], let code = keycodes[String(base)] {
      press(code, mods: ["shift"])
    } else {
      fail("no US-layout key for \(String(reflecting: ch))")
    }
  }
case "key" where args.count >= 2:
  guard let code = keycodes[args[1].lowercased()] else { fail("unknown key '\(args[1])'") }
  let mods = args.dropFirst(2).map { $0.lowercased() }
  for name in mods where modifiers[name] == nil { fail("unknown modifier '\(name)'") }
  press(code, mods: Array(mods))
default:
  fail("usage: hidtype type <text> | hidtype key <name> [shift|cmd|option|ctrl ...]")
}
