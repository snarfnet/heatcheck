import SwiftUI

@main
struct HeatCheckApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(AdService.shared)
                .task {
                    await AdService.shared.start()
                }
        }
    }
}
