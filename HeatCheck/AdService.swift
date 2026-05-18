import GoogleMobileAds
import SwiftUI
import UIKit

enum AdPlacement {
    case top
    case bottom
}

struct AdConfiguration {
    static let sampleBannerUnitID = "ca-app-pub-3940256099942544/2435281174"

    static func bannerUnitID(for placement: AdPlacement) -> String {
        switch placement {
        case .top:
            return bundleValue(for: "GADTopBannerAdUnitID", fallback: sampleBannerUnitID)
        case .bottom:
            return bundleValue(for: "GADBottomBannerAdUnitID", fallback: sampleBannerUnitID)
        }
    }

    static func request() -> Request {
        let request = Request()
        let extras = Extras()
        extras.additionalParameters = ["npa": "1"]
        request.register(extras)
        return request
    }

    private static func bundleValue(for key: String, fallback: String) -> String {
        guard let value = Bundle.main.object(forInfoDictionaryKey: key) as? String,
              !value.isEmpty,
              !value.hasPrefix("$(") else {
            return fallback
        }
        return value
    }
}

@MainActor
final class AdService: ObservableObject {
    static let shared = AdService()

    @Published private(set) var isReady = false

    private init() {}

    func start() async {
        guard !isReady else { return }
        MobileAds.shared.requestConfiguration.publisherPrivacyPersonalizationState = .disabled
        await MobileAds.shared.start()
        isReady = true
    }
}

struct AdBannerSlotView: View {
    let placement: AdPlacement
    @EnvironmentObject private var adService: AdService

    var body: some View {
        if adService.isReady {
            BannerViewContainer(adUnitID: AdConfiguration.bannerUnitID(for: placement))
                .frame(width: AdSizeBanner.size.width, height: AdSizeBanner.size.height)
                .frame(maxWidth: .infinity)
                .background(Color.white.opacity(0.92))
                .accessibilityLabel("広告")
        }
    }
}

private struct BannerViewContainer: UIViewRepresentable {
    let adUnitID: String

    func makeUIView(context: Context) -> BannerView {
        let banner = BannerView(adSize: AdSizeBanner)
        banner.adUnitID = adUnitID
        banner.rootViewController = UIApplication.shared.adRootViewController
        banner.load(AdConfiguration.request())
        return banner
    }

    func updateUIView(_ banner: BannerView, context: Context) {
        if banner.adUnitID != adUnitID {
            banner.adUnitID = adUnitID
            banner.load(AdConfiguration.request())
        }
    }
}

private extension UIApplication {
    var adRootViewController: UIViewController? {
        connectedScenes
            .compactMap { $0 as? UIWindowScene }
            .flatMap(\.windows)
            .first { $0.isKeyWindow }?
            .rootViewController?
            .topPresentedViewController
    }
}

private extension UIViewController {
    var topPresentedViewController: UIViewController {
        presentedViewController?.topPresentedViewController ?? self
    }
}
