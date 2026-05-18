import SwiftUI
import UIKit

struct ContentView: View {
    @StateObject private var thermalManager = ThermalManager()

    var body: some View {
        ZStack {
            backgroundGradient(for: thermalManager.state)
                .ignoresSafeArea()

            VStack(spacing: 0) {
                AdBannerSlotView(placement: .top)

                ScrollView {
                    VStack(spacing: 16) {
                        Text("発熱スマホお知らせ")
                            .font(.system(size: 26, weight: .bold))
                            .foregroundColor(.white)
                            .multilineTextAlignment(.center)

                        statusPanel

                        CharacterView(state: thermalManager.state, text: thermalManager.currentLine)

                        actionGrid

                        if thermalManager.shouldShowTips {
                            CoolingTipsView()
                        }
                    }
                    .padding(16)
                }

                AdBannerSlotView(placement: .bottom)
            }
        }
        .onAppear {
            thermalManager.startMonitoring()
        }
    }

    private var statusPanel: some View {
        VStack(spacing: 10) {
            Text("現在の熱状態")
                .font(.system(size: 15, weight: .semibold))
                .foregroundColor(.white.opacity(0.82))

            Text(thermalManager.stateText)
                .font(.system(size: 48, weight: .bold))
                .foregroundColor(.white)
                .minimumScaleFactor(0.7)

            Text(thermalManager.statusDetail)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.white.opacity(0.9))
                .multilineTextAlignment(.center)
                .lineSpacing(3)

            Text("iOSの熱状態をもとにした目安です。実測温度や故障診断ではありません。")
                .font(.system(size: 11, weight: .medium))
                .foregroundColor(.white.opacity(0.72))
                .multilineTextAlignment(.center)
                .lineSpacing(2)
        }
        .frame(maxWidth: .infinity)
        .padding(16)
        .background(Color.black.opacity(0.20))
        .cornerRadius(8)
    }

    private var actionGrid: some View {
        VStack(spacing: 12) {
            HStack(spacing: 12) {
                ActionButton(systemName: "sun.min", label: "明るさ", action: {
                    thermalManager.userAction(.dimScreen)
                })

                ActionButton(systemName: "iphone", label: "ケース", action: {
                    thermalManager.userAction(.removeCase)
                })

                ActionButton(systemName: "pause.circle", label: "休憩", action: {
                    thermalManager.userAction(.pauseApp)
                })
            }

            HStack(spacing: 12) {
                ActionButton(systemName: "bolt.slash", label: "充電停止", action: {
                    thermalManager.userAction(.unplug)
                })

                ActionButton(systemName: "battery.50", label: "低電力", action: {
                    thermalManager.userAction(.lowPower)
                })
            }
        }
        .padding(.horizontal)
    }

    private func backgroundGradient(for state: ThermalState) -> LinearGradient {
        let colors: [Color]
        switch state {
        case .cool:
            colors = [Color(red: 0.22, green: 0.56, blue: 0.92), Color(red: 0.13, green: 0.75, blue: 0.78)]
        case .normal:
            colors = [Color(red: 0.22, green: 0.62, blue: 0.78), Color(red: 0.28, green: 0.78, blue: 0.48)]
        case .warm:
            colors = [Color(red: 0.94, green: 0.64, blue: 0.23), Color(red: 0.89, green: 0.32, blue: 0.28)]
        case .hot:
            colors = [Color(red: 0.95, green: 0.36, blue: 0.26), Color(red: 0.68, green: 0.20, blue: 0.38)]
        case .critical:
            colors = [Color(red: 0.75, green: 0.16, blue: 0.25), Color(red: 0.35, green: 0.16, blue: 0.38)]
        case .recovering:
            colors = [Color(red: 0.22, green: 0.55, blue: 0.78), Color(red: 0.20, green: 0.38, blue: 0.72)]
        }

        return LinearGradient(gradient: Gradient(colors: colors), startPoint: .topLeading, endPoint: .bottomTrailing)
    }
}

struct ActionButton: View {
    let systemName: String
    let label: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 6) {
                Image(systemName: systemName)
                    .font(.system(size: 22, weight: .semibold))
                Text(label)
                    .font(.system(size: 12, weight: .semibold))
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .frame(height: 70)
            .background(Color.white.opacity(0.20))
            .cornerRadius(8)
        }
    }
}

struct CharacterView: View {
    let state: ThermalState
    let text: String

    private var imageSize: CGFloat {
        let screen = UIScreen.main.bounds
        if screen.height < 700 {
            return min(screen.width * 0.78, 260)
        }
        if screen.height < 850 {
            return min(screen.width * 0.82, 310)
        }
        return min(screen.width * 0.86, 360)
    }

    private var imageName: String {
        HeatGirlExpression.imageName(for: state, line: text)
    }

    var body: some View {
        VStack(spacing: 8) {
            Image(imageName)
                .resizable()
                .scaledToFit()
                .frame(width: imageSize, height: imageSize)
                .scaleEffect(state == .critical ? 1.08 : 1.0)
                .shadow(color: Color.black.opacity(0.18), radius: 14, x: 0, y: 8)
                .accessibilityHidden(true)

            Text("「\(text)」")
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(.white)
                .padding(12)
                .frame(maxWidth: .infinity)
                .background(Color.white.opacity(0.20))
                .cornerRadius(8)
                .lineLimit(2)
                .multilineTextAlignment(.center)
        }
    }
}

struct HeatGirlExpression {
    static func imageName(for state: ThermalState, line: String) -> String {
        let stateName: String
        switch state {
        case .cool:
            stateName = "cool"
        case .normal:
            stateName = "normal"
        case .warm:
            stateName = "warm"
        case .hot:
            stateName = "hot"
        case .critical:
            stateName = "critical"
        case .recovering:
            stateName = "recovering"
        }

        return "heatgirl_\(stateName)_\(String(format: "%02d", stableExpressionIndex(for: line)))"
    }

    private static func stableExpressionIndex(for line: String) -> Int {
        let seed = line.unicodeScalars.reduce(0) { partial, scalar in
            (partial + Int(scalar.value)) % 9973
        }
        return (seed % 5) + 1
    }
}

struct CoolingTipsView: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("熱を持った時の対策")
                .font(.system(size: 14, weight: .bold))
                .foregroundColor(.white)

            VStack(alignment: .leading, spacing: 6) {
                TipRow("画面の明るさを下げる")
                TipRow("ケースを外して風通しをよくする")
                TipRow("充電や重いアプリを少し休ませる")
                TipRow("直射日光を避け、涼しい場所に置く")
            }
            .font(.system(size: 12, weight: .medium))
            .foregroundColor(.white.opacity(0.92))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(Color.black.opacity(0.24))
        .cornerRadius(8)
    }
}

struct TipRow: View {
    let text: String

    init(_ text: String) {
        self.text = text
    }

    var body: some View {
        HStack(alignment: .top, spacing: 6) {
            Text("-")
            Text(text)
        }
    }
}

#Preview {
    ContentView()
}
