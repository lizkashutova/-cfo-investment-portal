import Foundation
import CoreGraphics
import ImageIO

let inputPath = "/Users/lizasutova/.gemini/antigravity/brain/e67f989e-54ea-4120-8a2a-7c0d3149e316/frame_0.0.png"
let outputPath = "/Users/lizasutova/.gemini/antigravity/scratch/cfo-investment-portal/dashboard_preview.png"

guard let imageSource = CGImageSourceCreateWithURL(URL(fileURLWithPath: inputPath) as CFURL, nil),
      let cgImage = CGImageSourceCreateImageAtIndex(imageSource, 0, nil) else {
    print("Failed to load image")
    exit(1)
}

let width = cgImage.width
let height = cgImage.height

let colorSpace = CGColorSpaceCreateDeviceRGB()
let bytesPerPixel = 4
let bytesPerRow = width * bytesPerPixel
let bitsPerComponent = 8
let bitmapInfo = CGImageAlphaInfo.premultipliedLast.rawValue | CGBitmapInfo.byteOrder32Big.rawValue

guard let context = CGContext(data: nil,
                              width: width,
                              height: height,
                              bitsPerComponent: bitsPerComponent,
                              bytesPerRow: bytesPerRow,
                              space: colorSpace,
                              bitmapInfo: bitmapInfo) else {
    print("Failed to create context")
    exit(1)
}

context.draw(cgImage, in: CGRect(x: 0, y: 0, width: width, height: height))

guard let pixelData = context.data else {
    print("Failed to get pixel data")
    exit(1)
}

let buffer = pixelData.assumingMemoryBound(to: UInt8.self)

// Flood fill queue
var queue: [(Int, Int)] = []
var visited = Array(repeating: Array(repeating: false, count: height), count: width)

// Background is white/light. We check if pixel is white.
func isWhite(x: Int, y: Int) -> Bool {
    let offset = (y * width + x) * bytesPerPixel
    let r = buffer[offset]
    let g = buffer[offset + 1]
    let b = buffer[offset + 2]
    // White is 255, 255, 255.
    // Let's use a threshold like > 220 to account for compression noise.
    return r > 220 && g > 220 && b > 220
}

// Add edges to queue
for y in 0..<height {
    if isWhite(x: 0, y: y) && !visited[0][y] {
        visited[0][y] = true
        queue.append((0, y))
    }
    if isWhite(x: width - 1, y: y) && !visited[width - 1][y] {
        visited[width - 1][y] = true
        queue.append((width - 1, y))
    }
}
for x in 0..<width {
    if isWhite(x: x, y: 0) && !visited[x][0] {
        visited[x][0] = true
        queue.append((x, 0))
    }
    if isWhite(x: x, y: height - 1) && !visited[x][height - 1] {
        visited[x][height - 1] = true
        queue.append((x, height - 1))
    }
}

var head = 0
let dx = [1, -1, 0, 0]
let dy = [0, 0, 1, -1]

while head < queue.count {
    let (cx, cy) = queue[head]
    head += 1
    
    for i in 0..<4 {
        let nx = cx + dx[i]
        let ny = cy + dy[i]
        
        if nx >= 0 && nx < width && ny >= 0 && ny < height {
            if !visited[nx][ny] && isWhite(x: nx, y: ny) {
                visited[nx][ny] = true
                queue.append((nx, ny))
            }
        }
    }
}

// Set white background pixels to transparent, and blend edges smoothly
for y in 0..<height {
    for x in 0..<width {
        let offset = (y * width + x) * bytesPerPixel
        if visited[x][y] {
            buffer[offset] = 0
            buffer[offset + 1] = 0
            buffer[offset + 2] = 0
            buffer[offset + 3] = 0
        } else {
            // Check neighbors to apply anti-aliasing / soft edge
            var hasVisitedNeighbor = false
            for i in 0..<4 {
                let nx = x + dx[i]
                let ny = y + dy[i]
                if nx >= 0 && nx < width && ny >= 0 && ny < height {
                    if visited[nx][ny] {
                        hasVisitedNeighbor = true
                        break
                    }
                }
            }
            if hasVisitedNeighbor {
                let r = buffer[offset]
                let g = buffer[offset + 1]
                let b = buffer[offset + 2]
                let avg = (Double(r) + Double(g) + Double(b)) / 3.0
                if avg > 200 {
                    // Transition pixel: set its transparency based on brightness to smooth out edges
                    let alpha = UInt8((255.0 - avg) / 55.0 * 255.0)
                    buffer[offset + 3] = alpha
                }
            }
        }
    }
}

guard let newCGImage = context.makeImage() else {
    print("Failed to make image")
    exit(1)
}

let outputURL = URL(fileURLWithPath: outputPath)
guard let destination = CGImageDestinationCreateWithURL(outputURL as CFURL, "public.png" as CFString, 1, nil) else {
    print("Failed to create destination")
    exit(1)
}

CGImageDestinationAddImage(destination, newCGImage, nil)
if CGImageDestinationFinalize(destination) {
    print("Successfully saved transparent image to \(outputPath)")
} else {
    print("Failed to save image")
    exit(1)
}
