import SwiftUI
import AppTrackingTransparency

@main
struct HeatCheckApp: App {
    @State private var attRequested = false

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(AdService.shared)
                .task {
                    await AdService.shared.start()
                }
                .onReceive(NotificationCenter.default.publisher(for: UIApplication.didBecomeActiveNotification)) { _ in
                    guard !attRequested else { return }
                    attRequested = true
                    DispatchQueue.main.asyncAfter(deadline: .now() + 1.0) {
                        ATTrackingManager.requestTrackingAuthorization { _ in }
                    }
                }
        }
    }
}
