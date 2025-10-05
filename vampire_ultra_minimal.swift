#!/usr/bin/env swift

import Foundation

while true {
    let task = Process()
    task.executableURL = URL(fileURLWithPath: "/usr/bin/env")
    task.arguments = ["vampire"]
    try? task.run()
    task.waitUntilExit()
    exit(0)
}
