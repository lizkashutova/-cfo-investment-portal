import Foundation
import CoreGraphics
import ImageIO

let inputPath = "/Users/lizasutova/.gemini/antigravity/brain/e67f989e-54ea-4120-8a2a-7c0d3149e316/frame_0.0.png"
guard let imageSource = CGImageSourceCreateWithURL(URL(fileURLWithPath: inputPath) as CFURL, nil),
      let cgImage = CGImageSourceCreateImageAtIndex(imageSource, 0, nil) else {
    print("Failed to load image")
    exit(1)
}

let width = cgImage.width
let height = cgImage.height
print("Image resolution: \(width)x\(height)")

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
    print("Failed to get data")
    exit(1)
}
let buffer = pixelData.assumingMemoryBound(to: UInt8.self)

// Inspect a row in the upper-middle of the laptop (e.g. y = height / 2)
let targetY = height / 2
print("Colors across row y=\(targetY) at different x columns:")
for percent in [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 99] {
    let targetX = width * percent / 100
    let offset = (targetY * width + targetX) * bytesPerPixel
    let r = buffer[offset]
    let g = buffer[offset + 1]
    let b = buffer[offset + 2]
    print("x=\(targetX) (\(percent)%): RGB=(\(r), \(g), \(b))")
}

// Let's also check the bottom area near the silver case (e.g. y = height - 50)
let bottomY = height - 50
print("\nColors across bottom row y=\(bottomY):")
for percent in [10, 20, 30, 40, 50, 60, 70, 80, 90] {
    let targetX = width * percent / 100
    let offset = (bottomY * width + targetX) * bytesPerPixel
    let r = buffer[offset]
    let g = buffer[offset + 1]
    let b = buffer[offset + 2]
    print("x=\(targetX) (\(percent)%): RGB=(\(r), \(g), \(b))")
}
