import Foundation
import AVFoundation
import CoreGraphics
import ImageIO

let videoPath = "/Users/lizasutova/.gemini/antigravity/scratch/cfo-investment-portal/dashboard_preview.mp4"
let outputPath = "/Users/lizasutova/.gemini/antigravity/brain/e67f989e-54ea-4120-8a2a-7c0d3149e316/extracted_video_frame.png"

let url = URL(fileURLWithPath: videoPath)
let asset = AVAsset(url: url)
let generator = AVAssetImageGenerator(asset: asset)
generator.appliesPreferredTrackTransform = true

// Request frame at 1 second
let time = CMTime(seconds: 1.0, preferredTimescale: 600)
do {
    let cgImage = try generator.copyCGImage(at: time, actualTime: nil)
    let outputURL = URL(fileURLWithPath: outputPath)
    if let destination = CGImageDestinationCreateWithURL(outputURL as CFURL, "public.png" as CFString, 1, nil) {
        CGImageDestinationAddImage(destination, cgImage, nil)
        if CGImageDestinationFinalize(destination) {
            print("Successfully saved frame to \(outputPath)")
        } else {
            print("Failed to finalize image destination")
        }
    } else {
        print("Failed to create image destination")
    }
} catch {
    print("Error generating image: \(error)")
}
