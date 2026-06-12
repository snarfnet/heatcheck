import SwiftUI
import AppTrackingTransparency
import UIKit

@main
struct HeatCheckApp: App {
    @State private var didRunAdStartup = false

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(AdService.shared)
                .task {
                    guard !didRunAdStartup,
                          UIApplication.shared.applicationState == .active else { return }
                    didRunAdStartup = true
                    await requestTrackingAuthorizationThenStartAds()
                }
                .onReceive(NotificationCenter.default.publisher(for: UIApplication.didBecomeActiveNotification)) { _ in
                    guard !didRunAdStartup else { return }
                    didRunAdStartup = true
                    Task {
                        await requestTrackingAuthorizationThenStartAds()
                    }
                }
        }
    }

    @MainActor
    private func requestTrackingAuthorizationThenStartAds() async {
        if ATTrackingManager.trackingAuthorizationStatus == .notDetermined {
            try? await Task.sleep(nanoseconds: 500_000_000)
            let _: ATTrackingManager.AuthorizationStatus = await withCheckedContinuation { continuation in
                ATTrackingManager.requestTrackingAuthorization { status in
                    continuation.resume(returning: status)
                }
            }
        }

        await AdService.shared.start()
    }
}
