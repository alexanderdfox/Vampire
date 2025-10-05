#!/usr/bin/env swift

import Foundation

// Vampire HTTP Server with self-killing fork structure (Swift-compatible)
class VampireHTTPServer {
    private let port: UInt16
    private var running = true
    
    init(port: UInt16 = 8000) {
        self.port = port
    }
    
    func start() {
        print("🧛 Vampire HTTP Server starting on port \(port)...")
        
        // Create HTTP server socket
        let serverSocket = socket(AF_INET, SOCK_STREAM, 0)
        guard serverSocket != -1 else {
            print("❌ Failed to create socket")
            return
        }
        
        // Set socket options
        var opt = 1
        setsockopt(serverSocket, SOL_SOCKET, SO_REUSEADDR, &opt, socklen_t(MemoryLayout<Int>.size))
        
        // Bind socket
        var address = sockaddr_in()
        address.sin_family = sa_family_t(AF_INET)
        address.sin_addr.s_addr = inet_addr("127.0.0.1")
        address.sin_port = port.bigEndian
        
        let bindResult = withUnsafePointer(to: &address) {
            $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                bind(serverSocket, $0, socklen_t(MemoryLayout<sockaddr_in>.size))
            }
        }
        
        guard bindResult == 0 else {
            print("❌ Failed to bind to port \(port)")
            close(serverSocket)
            return
        }
        
        // Listen for connections
        guard listen(serverSocket, 5) == 0 else {
            print("❌ Failed to listen")
            close(serverSocket)
            return
        }
        
        print("🌐 Vampire server listening on http://localhost:\(port)")
        print("⚡ Self-killing fork structure active...")
        
        // Main server loop with self-killing fork
        while running {
            // Accept connection
            var clientAddress = sockaddr_in()
            var clientAddressLength = socklen_t(MemoryLayout<sockaddr_in>.size)
            
            let clientSocket = withUnsafeMutablePointer(to: &clientAddress) {
                $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                    accept(serverSocket, $0, &clientAddressLength)
                }
            }
            
            if clientSocket != -1 {
                handleClient(clientSocket)
                close(clientSocket)
            }
            
            // Self-killing fork: spawn new process and kill current (using Process)
            let newServer = Process()
            newServer.executableURL = URL(fileURLWithPath: "/usr/bin/env")
            newServer.arguments = ["./vampire_http_server"]
            
            do {
                try newServer.run()
                close(serverSocket)
                exit(0)  // Kill current process
            } catch {
                print("❌ Failed to spawn new server: \(error)")
                break
            }
        }
        
        close(serverSocket)
    }
    
    private func handleClient(_ clientSocket: Int32) {
        var buffer = [UInt8](repeating: 0, count: 1024)
        let bytesRead = read(clientSocket, &buffer, buffer.count)
        
        if bytesRead > 0 {
            let request = String(cString: buffer)
            let response = generateResponse(for: request)
            
            _ = response.withCString { cString in
                write(clientSocket, cString, strlen(cString))
            }
        }
    }
    
    private func generateResponse(for request: String) -> String {
        // Try to read vampire.html file
        if let htmlContent = try? String(contentsOfFile: "vampire.html", encoding: .utf8) {
            return """
            HTTP/1.1 200 OK\r
            Content-Type: text/html; charset=utf-8\r
            Content-Length: \(htmlContent.count)\r
            Cache-Control: no-store\r
            \r
            \(htmlContent)
            """
        } else {
            // Fallback if vampire.html not found
            let fallbackHtml = """
            <!DOCTYPE html>
            <html>
            <head><title>🧛 Vampire HTTP Server</title></head>
            <body style="font-family:monospace;background:#000;color:#0f0;margin:20px;">
            <h1>🧛 Vampire HTTP Server</h1>
            <p>Self-killing fork structure active</p>
            <p>Process ID: \(getpid())</p>
            <p>Time: \(Date())</p>
            <p>⚡ Server continuously spawns and kills itself</p>
            <p>❌ vampire.html not found</p>
            </body>
            </html>
            """
            
            return """
            HTTP/1.1 200 OK\r
            Content-Type: text/html\r
            Content-Length: \(fallbackHtml.count)\r
            \r
            \(fallbackHtml)
            """
        }
    }
}

// Start the vampire HTTP server
let server = VampireHTTPServer()
server.start()
