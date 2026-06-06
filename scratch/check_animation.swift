import Foundation
import AVFoundation
import CoreGraphics
import ImageIO

let videoPath = "/Users/lizasutova/.gemini/antigravity/scratch/cfo-investment-portal/dashboard_preview.mp4"
let url = URL(fileURLWithPath: videoPath)
let asset = AVAsset(url: url)

let generator = AVAssetImageGenerator(asset: asset)
generator.appliesPreferredTrackTransform = true

for timeInSeconds in [0.0, 1.5, 3.0, 4.5] {
    let time = CMTime(seconds: timeInSeconds, preferredTimescale: 600)
    do {
        let cgImage = try generator.copyCGImage(at: time, actualTime: nil)
        let outputPath = "/Users/lizasutova/.gemini/antigravity/brain/e67f989e-54ea-4120-8a2a-7c0d3149e316/frame_\(timeInSeconds).png"
        let outputURL = URL(fileURLWithPath: outputPath)
        if let destination = CGImageDestinationCreateWithURL(outputURL as CFURL, "public.png" as CFString, 1, nil) {
            CGImageDestinationAddImage(destination, cgImage, nil)
            _ = CGImageDestinationFinalize(destination)
            print("Saved frame at \(timeInSeconds)s")
        }
    } catch {
        print("No frame at \(timeInSeconds)s or error: \(error)")
    }
}
