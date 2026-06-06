import Foundation
import AVFoundation
import CoreGraphics
import ImageIO
import CommonCrypto

let videoPath = "/Users/lizasutova/.gemini/antigravity/scratch/cfo-investment-portal/dashboard_preview.mp4"
let url = URL(fileURLWithPath: videoPath)
let asset = AVAsset(url: url)

let generator = AVAssetImageGenerator(asset: asset)
generator.appliesPreferredTrackTransform = true
generator.requestedTimeToleranceBefore = .zero
generator.requestedTimeToleranceAfter = .zero

func md5(data: Data) -> String {
    var hash = [UInt8](repeating: 0, count: Int(CC_MD5_DIGEST_LENGTH))
    data.withUnsafeBytes {
        _ = CC_MD5($0.baseAddress, CC_LONG(data.count), &hash)
    }
    return hash.map { String(format: "%02x", $0) }.joined()
}

for t in 0...10 {
    let time = CMTime(seconds: Double(t), preferredTimescale: 600)
    do {
        let cgImage = try generator.copyCGImage(at: time, actualTime: nil)
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
            print("Failed to create context for \(t)s")
            continue
        }
        
        context.draw(cgImage, in: CGRect(x: 0, y: 0, width: width, height: height))
        if let data = context.data {
            let bufferSize = width * height * bytesPerPixel
            let dataNS = Data(bytes: data, count: bufferSize)
            let hashStr = md5(data: dataNS)
            print("Time \(t)s: MD5 = \(hashStr)")
        }
    } catch {
        print("Error at \(t)s: \(error)")
    }
}
